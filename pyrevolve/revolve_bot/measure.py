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

    def count_branching_bricks(self, module=None):
        """Count amount of fully branching modules
        """
        try:
            if module is None:
                module = self.body

            if module.has_children():
                children_count = sum(1 for _ in module.iter_children())
                if (isinstance(module, BrickModule) and children_count == 3) or (isinstance(module, CoreModule) and children_count == 4):
                    self.branching_modules_count += 1
                for core_slot, child_module in module.iter_children():
                    if child_module is None:
                        continue
                    self.count_branching_bricks(child_module)
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
        practical_limit_branching_bricks = math.floor((self.absolute_size-2)/3)
        self.branching = self.branching_modules_count / practical_limit_branching_bricks
        return self.branching

    def calculate_extremities(self, module=None):
        """
        Calculate extremities in body
        """
        pass

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
            practical_limit_limbs = 2 * math.floor((self.absolute_size-6)/3) + (self.absolute_size - 6) % 3 + 4
        self.calculate_extremities()
        self.limbs = self.extremities / practical_limit_limbs
        return self.limbs

    def calculate_extensiveness(self, module=None):
        """
        Calculate extensiveness of body
        """
        pass

    def measure_length_of_limbs(self):
        """
        Measure length of limbs
        :return:
        """
        if self.absolute_size is None:
            self.measure_absolute_size()
        if self.absolute_size < 3:
            self.length_of_limbs = 0
            return self.length_of_limbs
        self.calculate_extensiveness()
        practical_limit_extensiveness = self.absolute_size - 2
        self.length_of_limbs = self.extensiveness / practical_limit_extensiveness
        return self.length_of_limbs

    def measure_symmetry(self):
        """
        Measure symmetry
        """
        try:
            # Get coordinates of horizontal grid
            render = Render()
            render.traverse_path_of_robot(self.body, 0, False, True)
            # Modules branching to the left of the core
            horizontal_coordinates = render.grid.visited_coordinates
            render = Render()
            render.traverse_path_of_robot(self.body, 0, False, True, False, True)
            render.grid.visited_coordinates
            # Modules branching to the right of the core
            horizontal_mirror_coordinates = render.grid.visited_coordinates

            # Calculate horizontal symmetry
            mirrored_modules_horizontal = 0
            for module in horizontal_coordinates:
                if [-module[0], module[1]] in horizontal_mirror_coordinates:
                    mirrored_modules_horizontal += 1

            total_modules_horizontal = len(horizontal_coordinates) + len(horizontal_mirror_coordinates)
            horizontal_symmetry = mirrored_modules_horizontal / total_modules_horizontal


            # Get coordinates of vertical grid
            render = Render()
            render.traverse_path_of_robot(self.body, 0, False, False, True)
            # Modules branching to the top of the core
            vertical_coordinates = render.grid.visited_coordinates
            render = Render()
            render.traverse_path_of_robot(self.body, 0, False, False, True, True)
            # Modules branching to the bottom of the core            
            vertical_mirror_coordinates = render.grid.visited_coordinates

            # Calculate vertical symmetry
            mirrored_modules_vertical = 0
            for module in vertical_coordinates:
                if [module[0], -module[1]] in vertical_mirror_coordinates:
                    mirrored_modules_vertical += 1

            total_modules_vertical = len(vertical_coordinates) + len(vertical_mirror_coordinates)
            vertical_symmetry = mirrored_modules_vertical / total_modules_vertical

            self.symmetry = max(horizontal_symmetry, vertical_symmetry)
            return self.symmetry

        except Exception as e:
            print('Failed measuring width and height')
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
            return self.joints
        self.count_active_hinges()
        practical_limit_active_hinges = math.floor((self.absolute_size-1)/2)
        self.joints = self.active_hinges_count / practical_limit_active_hinges
        return self.joints

    def measure_proportion(self):
        """Meaure proportion, specified by the 2d ratio of the body
        :return:
        """
        if self.width is None or self.height is None:
            self.measure_width_height()
        if self.width < self.height:
            self.proportion = self.width / self.height
        else
        self.proportion = self.height / self.width
        return self.proportion

    def measure_absolute_size(self, module=None):
        """
        Count total amount of modules in body excluding sensors
        :return:
        """
        try:
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
        """
        return self.get_all_measurements()

    def get_all_measurements(self):
        """
        Return dict of all measurements
        :return:
        """
        return {
            'branching': self.branching,
            'limbs': self.limbs,
            'length_of_limbs': self.length_of_limbs,
            'coverage': self.coverage,
            'joints': self.joints,
            'proportion': self.proportion,
            'width': self.width,
            'height': self.height,
            'absolute_size': self.absolute_size,
            'size': self.size
            'symmetry': self.symmetry
        }
