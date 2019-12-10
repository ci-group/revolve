import math
from pyrevolve.custom_logging.logger import logger
from pyrevolve.revolve_bot.render.render import Render
from pyrevolve.revolve_bot.render.grid import Grid
from pyrevolve.revolve_bot.revolve_module import ActiveHingeModule, BrickModule, TouchSensorModule, BrickSensorModule, CoreModule


class MeasureBody2D:
    def __init__(self, body):
        self.body = body

        # Absolute branching
        self.branching_modules_count = None
        # Relative branching
        self.branching = None
        # Absolute number of limbs
        self.extremities = None
        # Relative number of limbs
        self.limbs = None
        # Absolute length of limbs
        self.extensiveness = None
        # Relative length of limbs
        self.length_of_limbs = None
        # Coverage
        self.coverage = None
        # Relative number of effective active joints
        self.joints = None
        # Absolute number of effective active joints
        self.active_hinges_count = None
        # Proportion
        self.proportion = None
        # Width
        self.width = None
        # Height
        self.height = None
        # Absolute size
        self.absolute_size = None
        # Relative size in respect of the max body size `self.max_permitted_modules`
        self.size = None
        # Proportion of sensor vs empty slots
        self.sensors = None
        # Body symmetry
        self.symmetry = None
        # Number of active joints
        self.hinge_count = None
        # Number of bricks
        self.brick_count = None
        # Number of brick sensors
        self.brick_sensor_count = None
        # Number of touch sensors
        self.touch_sensor_count = None
        # Number of free slots
        self.free_slots = None
        # Maximum number of modules allowed (sensors excluded)
        self.max_permitted_modules = None

    def count_branching_bricks(self, module=None, init=True):
        """
        Count amount of fully branching modules in body
        """
        try:
            if init:
                self.branching_modules_count = 0
            if module is None:
                module = self.body

            if module.has_children():
                children_count = 0
                for core_slot, child_module in module.iter_children():
                    if child_module is None:
                        continue
                    if not isinstance(child_module, TouchSensorModule) and not isinstance(child_module, BrickSensorModule):
                        children_count += 1
                    self.count_branching_bricks(child_module, False)
                if (isinstance(module, BrickModule) and children_count == 3) or (isinstance(module, CoreModule) and children_count == 4):
                    self.branching_modules_count += 1
        except Exception as e:
            logger.exception(f'Exception: {e}. \nFailed counting branching bricks')

    def measure_branching(self):
        """
        Measure branching by dividing fully branching by possible branching modules
        """
        if self.absolute_size is None:
            self.measure_absolute_size()
        if self.branching_modules_count is None:
            self.count_branching_bricks()
        if self.branching_modules_count == 0 or self.absolute_size < 5:
            self.branching = 0
            return self.branching
        practical_limit_branching_bricks = math.floor((self.absolute_size-2)/3)
        self.branching = self.branching_modules_count / practical_limit_branching_bricks
        return self.branching

    def calculate_extremities_extensiveness(self, module=None, extremities=False, extensiveness=False, init=True):
        """
        Calculate extremities or extensiveness in body
        @param extremities: calculate extremities in body if true
        @param extensiveness: calculate extensiveness in body if true
        """
        try:
            if module is None:
                module = self.body
            if init and extremities:
                self.extremities = 0
            if init and extensiveness:
                self.extensiveness = 0

            children_count = 0
            for core_slot, child_module in module.iter_children():
                if child_module is None:
                    continue
                if not isinstance(child_module, TouchSensorModule):
                    children_count += 1
                self.calculate_extremities_extensiveness(child_module, extremities, extensiveness, False)
            if children_count == 0 and not (isinstance(module, CoreModule) or isinstance(module, TouchSensorModule)) and extremities:
                self.extremities += 1
            if children_count == 1 and not (isinstance(module, CoreModule) or isinstance(module, TouchSensorModule)) and extensiveness:
                self.extensiveness += 1
        except Exception as e:
            logger.exception(f'Exception: {e}. \nFailed calculating extremities or extensiveness')

    def measure_limbs(self):
        """
        Measure limbs
        :return:
        """
        if self.absolute_size is None:
            self.measure_absolute_size()
        practical_limit_limbs = None
        if self.absolute_size < 6:
            practical_limit_limbs = self.absolute_size - 1
        else:
            practical_limit_limbs = 2 * math.floor((self.absolute_size - 6) / 3) + ((self.absolute_size - 6) % 3) + 4

        if self.extremities is None:
            self.calculate_extremities_extensiveness(None, True, False)
        if self.extremities == 0:
            self.limbs = 0
            return 0
        self.limbs = self.extremities / practical_limit_limbs
        return self.limbs

    def measure_length_of_limbs(self):
        """
        Measure length of limbs
        :return:
        """
        if self.absolute_size is None:
            self.measure_absolute_size()
        if self.extensiveness is None:
            self.calculate_extremities_extensiveness(None, False, True)
        if self.absolute_size < 3:
            self.length_of_limbs = 0
            return self.length_of_limbs
        practical_limit_extensiveness = self.absolute_size - 2
        self.length_of_limbs = self.extensiveness / practical_limit_extensiveness
        return self.length_of_limbs

    def measure_symmetry(self):
        """
        Measure symmetry
        """
        try:
            render = Render()
            render.traverse_path_of_robot(self.body, 0, False)
            coordinates = render.grid.visited_coordinates

            horizontal_mirrored = 0
            horizontal_total = 0
            vertical_mirrored = 0
            vertical_total = 0
            # Calculate symmetry in body
            for position in coordinates:
                if position[0] is not 0:
                    horizontal_total += 1
                    if [-position[0], position[1]] in coordinates:
                        horizontal_mirrored += 1
                if position[1] is not 0:
                    vertical_total += 1
                    if [position[0], -position[1]] in coordinates:
                        vertical_mirrored += 1

            horizontal_symmetry = horizontal_mirrored / horizontal_total if horizontal_mirrored > 0 else 0
            vertical_symmetry = vertical_mirrored / vertical_total if vertical_mirrored > 0 else 0

            self.symmetry = max(horizontal_symmetry, vertical_symmetry)
            return self.symmetry

        except Exception as e:
            logger.exception(f'Exception: {e}. \nFailed measuring symmetry')

    def measure_coverage(self):
        """
        Measure the coverage of the robot, specified by the amount of modules
        divided by the spanning surface of the robot (excluding sensors)
        :return:
        """
        if self.absolute_size is None:
            self.measure_absolute_size()
        if self.width is None or self.height is None:
            self.measure_width_height()
        self.coverage = self.absolute_size / (self.width*self.height)
        return self.coverage

    def count_active_hinges(self, module=None, init=True):
        """
        Count amount of active hinges
        """
        try:
            if module is None:
                module = self.body
            if init:
                self.active_hinges_count = 0
            if module.has_children():
                if isinstance(module, ActiveHingeModule):
                    self.active_hinges_count += 1
                for core_slot, child_module in module.iter_children():
                    if child_module is None:
                        continue
                    self.count_active_hinges(child_module, False)
        except Exception as e:
            logger.exception(f'Exception: {e}. \nFailed calculating count')

    def measure_joints(self):
        """
        Measure joints, characterizing the possible amount of joints
        :return:
        """
        if self.absolute_size is None:
            self.measure_absolute_size()
        if self.active_hinges_count is None:
            self.count_active_hinges()
        if self.active_hinges_count == 0 or self.absolute_size < 3:
            self.joints = 0
            return self.joints
        practical_limit_active_hinges = self.absolute_size - 2
        self.joints = self.active_hinges_count / practical_limit_active_hinges
        return self.joints

    def measure_proportion(self):
        """
        Meaure proportion, specified by the 2d ratio of the body
        :return:
        """
        if self.width is None or self.height is None:
            self.measure_width_height()
        if self.width < self.height:
            self.proportion = self.width / self.height
        else:
            self.proportion = self.height / self.width
            return self.proportion

    def count_free_slots(self, module=None, init=True):
        """
        Count amount of free slots in body
        """
        if module is None:
            module = self.body
        if init:
            self.free_slots = 0
        children_count = 0
        for core_slot, child_module in module.iter_children():
            if child_module is None:
                continue
            if not isinstance(child_module, TouchSensorModule):
                children_count += 1
            self.count_free_slots(child_module, False)
        if isinstance(module, CoreModule):
            self.free_slots += (4-children_count)
        if isinstance(module, BrickModule):
            self.free_slots += (3-children_count)

    def measure_sensors(self, module=None):
        """
        Measurement describes the proportion of free slots that contain sensors
        """
        if self.free_slots is None:
            self.count_free_slots()
        if self.free_slots == 0:
            self.free_slots = 0.0001
        self.sensors = self.touch_sensor_count / self.free_slots
        return self.sensors

    def measure_absolute_size(self, module=None):
        """
        Count total amount of modules in body excluding sensors
        :return:
        """
        try:
            if self.absolute_size is None:
                self.calculate_count()
                self.absolute_size = self.brick_count + self.hinge_count + 1
            return self.absolute_size
        except Exception as e:
            logger.exception(f'Exception: {e}. \nFailed measuring absolute size')

    def calculate_count(self, module=None, init=True):
        """
        Count amount of modules for each distinct type
        """
        try:
            if init:
                self.hinge_count = 0
                self.brick_count = 0
                self.brick_sensor_count = 0
                self.touch_sensor_count = 0
            if module is None:
                module = self.body
            elif isinstance(module, ActiveHingeModule):
                self.hinge_count += 1
            elif isinstance(module, BrickModule):
                self.brick_count += 1
            elif isinstance(module, BrickSensorModule):
                self.brick_sensor_count += 1
            elif isinstance(module, TouchSensorModule):
                self.touch_sensor_count += 1

            if module.has_children():
                for core_slot, child_module in module.iter_children():
                    if child_module is None:
                        continue
                    self.calculate_count(child_module, False)
        except Exception as e:
            logger.exception(f'Exception: {e}. \nFailed calculating count')

    def measure_width_height(self):
        """
        Measure width and height of body, excluding sensors
        """
        try:
            render = Render()
            render.traverse_path_of_robot(self.body, 0, False)
            render.grid.calculate_grid_dimensions()
            self.width = render.grid.width
            self.height = render.grid.height
        except Exception as e:
            logger.exception(f'Exception: {e}. \nFailed measuring width and height')

    def measure_all(self):
        """
        Perform all measurements
        :return:
        """
        self.measure_limbs()
        self.measure_length_of_limbs()
        self.measure_width_height()
        self.measure_absolute_size()
        self.measure_proportion()
        self.measure_joints()
        self.measure_coverage()
        self.measure_symmetry()
        self.measure_branching()
        self.measure_sensors()
        return self.measurements_to_dict()

    def measurements_to_dict(self):
        """
        Return dict of all measurements
        :return:
        """
        return {
            'branching': self.branching,
            'branching_modules_count': self.branching_modules_count,
            'limbs': self.limbs,
            'extremities': self.extremities,
            'length_of_limbs': self.length_of_limbs,
            'extensiveness': self.extensiveness,
            'coverage': self.coverage,
            'joints': self.joints,
            'hinge_count': self.hinge_count,
            'active_hinges_count': self.active_hinges_count,
            'brick_count': self.brick_count,
            'touch_sensor_count': self.touch_sensor_count,
            'brick_sensor_count': self.brick_sensor_count,
            'proportion': self.proportion,
            'width': self.width,
            'height': self.height,
            'absolute_size': self.absolute_size,
            'sensors': self.sensors,
            'symmetry': self.symmetry
        }

    def __repr__(self):
        return self.measurements_to_dict().__repr__()