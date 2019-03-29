import math
from .render.render import Render
from .render.grid import Grid
from .revolve_module import ActiveHingeModule, BrickModule, TouchSensorModule, BrickSensorModule, CoreModule


class Measure:
    def __init__(self, body):
        self.body = body
        self.branching_modules_count = 0
        self.branching = None
        self.extremities = 0
        self.limbs = None
        self.extensiveness = 0
        self.length_of_limbs = None
        self.coverage = None
        self.joints = None
        self.proportion = None
        self.width = None
        self.height = None
        self.absolute_size = None
        self.size = None
        self.symmetry = None
        self.hinge_count = 0
        self.active_hinges_count = 0
        self.brick_count = 0
        self.brick_sensor_count = 0
        self.touch_sensor_count = 0
        self.max_permitted_modules = None

    def round(self, number, decimals):
        """
        Round number to nearest value to amount of decimals specified
        @param number: number to round
        @param decimals: number of decimals
        """
        return math.floor((number*(10**decimals)) + 0.5) / (10**decimals)

    def count_branching_bricks(self, module=None):
        """
        Count amount of fully branching modules in body
        """
        try:
            if module is None:
                module = self.body

            if module.has_children():
                children_count = 0
                for core_slot, child_module in module.iter_children():
                    if child_module is None:
                        continue
                    if not isinstance(child_module, TouchSensorModule) and not isinstance(child_module, BrickSensorModule):
                        children_count += 1
                    self.count_branching_bricks(child_module)
                if (isinstance(module, BrickModule) and children_count == 3) or (isinstance(module, CoreModule) and children_count == 4):
                    self.branching_modules_count += 1
        except Exception as e:
            print('Failed counting branching bricks')
            print('Exception: {}'.format(e))

    def measure_branching(self):
        """
        Measure branching by dividing fully branching by possible branching modules
        """
        if self.absolute_size is None:
            self.measure_absolute_size()
        if self.absolute_size < 5:
            self.branching = 0
            return self.branching
        self.count_branching_bricks()
        if self.branching_modules_count == 0:
            self.branching = 0
            return 0

        practical_limit_branching_bricks = math.floor((self.absolute_size-2)/3)
        self.branching = self.branching_modules_count / practical_limit_branching_bricks
        return self.branching

    def calculate_extremities_extensiveness(self, module=None, extremities=False, extensiveness=False):
        """
        Calculate extremities or extensiveness in body
        @param extremities: calculate extremities in body if true
        @param extensiveness: calculate extensiveness in body if true
        """
        try:
            if module is None:
                module = self.body

            children_count = 0
            for core_slot, child_module in module.iter_children():
                if child_module is None:
                    continue
                if not isinstance(child_module, TouchSensorModule):
                    children_count += 1
                if extremities:
                    self.calculate_extremities_extensiveness(child_module, True, False)
                if extensiveness:
                    self.calculate_extremities_extensiveness(child_module, False, True)
            if children_count == 0 and not (isinstance(module, CoreModule) or isinstance(module, TouchSensorModule)) and extremities:
                self.extremities += 1
            if children_count == 1 and not (isinstance(module, CoreModule) or isinstance(module, TouchSensorModule)) and extensiveness:
                self.extensiveness += 1
        except Exception as e:
            print('Failed calculating extremities or extensiveness')
            print('Exception: {}'.format(e))

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
        if self.absolute_size < 3:
            self.length_of_limbs = 0
            return 0
        self.calculate_extremities_extensiveness(None, False, True)
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
            print('Failed measuring symmetry')
            print('Exception: {}'.format(e))

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

    def count_active_hinges(self, module=None):
        """
        Count amount of active hinges
        """
        try:
            if module is None:
                module = self.body
            if module.has_children():
                if isinstance(module, ActiveHingeModule):
                    self.active_hinges_count += 1
                for core_slot, child_module in module.iter_children():
                    if child_module is None:
                        continue
                    self.count_active_hinges(child_module)
        except Exception as e:
            print('Failed calculating count')
            print('Exception: {}'.format(e))

    def measure_joints(self):
        """
        Measure joints, characterizing the possible amount of joints
        :return:
        """
        if self.absolute_size is None:
            self.measure_absolute_size()
        if self.absolute_size < 3:
            self.joints = 0
            return 0
        self.count_active_hinges()
        practical_limit_active_hinges = self.absolute_size - 2
        if self.active_hinges_count == 0:
            self.joints = 0
            return 0
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
            print('Failed measuring absolute size')
            print('Exception: {}'.format(e))

    def calculate_count(self, module=None):
        """
        Count amount of modules for each distinct type
        """
        try:
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
                    self.calculate_count(child_module)
        except Exception as e:
            print('Failed calculating count')
            print('Exception: {}'.format(e))

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
            print('Failed measuring width and height')
            print('Exception: {}'.format(e))

    def measure_size(self):
        """
        Measure size of robot, specified by the amount of modules divided by the limit
        :return: False if max_permitted_modules is None
        """
        if self.max_permitted_modules is None:
            return False
        if self.absolute_size is None:
            self.measure_absolute_size()
        self.size = self.absolute_size / self.max_permitted_modules

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
        return self.measurement_to_dict()

    def measurement_to_dict(self, round=False, decimals=3):
        """
        Return dict of all measurements
		@param round: round to amount of decimals if true
        @param decimals: amount of decimals
        :return:
        """
        if round:
            return {
                'branching': self.round(self.branching, decimals),
                'branching_modules_count': self.round(self.branching_modules_count, decimals),
                'limbs': self.round(self.limbs, 3),
                'extremeties': self.round(self.extremities, 3),
                'length_of_limbs': self.round(self.length_of_limbs, decimals),
                'extensiveness': self.round(self.extensiveness, decimals),
                'coverage': self.round(self.coverage, decimals),
                'joints': self.round(self.joints, decimals),
                'hinge_count': self.round(self.hinge_count, decimals),
                'active_hinges_count': self.round(self.active_hinges_count, decimals),
                'brick_count': self.round(self.brick_count, decimals),
                'touch_sensor_count': self.round(self.touch_sensor_count, decimals),
                'brick_sensor_count': self.round(self.brick_sensor_count, decimals),
                'proportion': self.round(self.proportion, decimals),
                'width': self.round(self.width, decimals),
                'height': self.round(self.height, decimals),
                'absolute_size': self.round(self.absolute_size, decimals),
                'size': self.round(self.size, decimals),
                'symmetry': self.round(self.symmetry, decimals)
            }

        return {
            'branching': self.branching,
            'branching_modules_count': self.branching_modules_count,
            'limbs': self.limbs,
            'extremeties': self.extremities,
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
            'size': self.size,
            'symmetry': self.symmetry
        }
