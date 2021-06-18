import math
from pyrevolve.custom_logging.logger import logger
from pyrevolve.revolve_bot.revolve_module import ActiveHingeModule, BrickModule, TouchSensorModule, BrickSensorModule, \
    CoreModule


class MeasureBody3D:
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
        # Z depth
        self.z_depth = None
        # Absolute size
        self.absolute_size = None
        # Relative size in respect of the max body size `self.max_permitted_modules`
        self.size = None
        # Proportion of sensor vs empty slots
        self.sensors = None
        # Body symmetry in the xy plane
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
        # Ratio of the height over the root of the area of the base
        self.height_base_ratio = None
        # Maximum number of modules allowed (sensors excluded)
        self.max_permitted_modules = None
        # Vertical symmetry
        self.symmetry_vertical = None
        # Base model density
        self.base_density = None
        # Bottom layer of the robot
        self.bottom_layer = None

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
                for _slot, child_module in module.iter_children():
                    if child_module is None:
                        continue
                    if not isinstance(child_module, TouchSensorModule) \
                            and not isinstance(child_module, BrickSensorModule):
                        children_count += 1
                    self.count_branching_bricks(child_module, False)
                if (isinstance(module, BrickModule) and children_count == 3) or \
                        (isinstance(module, CoreModule) and children_count == 4):
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
        practical_limit_branching_bricks = math.floor((self.absolute_size - 2) / 3)
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
            for _slot, child_module in module.iter_children():
                if child_module is None:
                    continue
                if not isinstance(child_module, TouchSensorModule):
                    children_count += 1
                self.calculate_extremities_extensiveness(child_module, extremities, extensiveness, False)
            if children_count == 0 \
                    and not (isinstance(module, CoreModule) or isinstance(module, TouchSensorModule)) \
                    and extremities:
                self.extremities += 1
            if children_count == 1 \
                    and not (isinstance(module, CoreModule) or isinstance(module, TouchSensorModule)) \
                    and extensiveness:
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

    def collect_all_coordinates(self, module=None):
        module = module or self.body
        coordinates = set()
        coordinates.add(module.substrate_coordinates)
        if module.has_children():
            for _slot, child_module in module.iter_children():
                if child_module is None:
                    continue
                children_coordinates = self.collect_all_coordinates(child_module)
                coordinates = coordinates.union(children_coordinates)
        return coordinates

    def measure_symmetry(self):
        """
        Measure symmetry in the xy plane of the robot.
        """
        try:
            coordinates = self.collect_all_coordinates()

            horizontal_mirrored = 0
            horizontal_total = 0
            vertical_mirrored = 0
            vertical_total = 0
            # Calculate xy symmetry in body
            for position in coordinates:
                if position[0] != 0:
                    horizontal_total += 1
                    if (-position[0], position[1], position[2]) in coordinates:
                        horizontal_mirrored += 1
                if position[1] != 0:
                    vertical_total += 1
                    if (position[0], -position[1], position[2]) in coordinates:
                        vertical_mirrored += 1

            horizontal_symmetry = horizontal_mirrored / horizontal_total if horizontal_mirrored > 0 else 0
            vertical_symmetry = vertical_mirrored / vertical_total if vertical_mirrored > 0 else 0

            self.symmetry = max(horizontal_symmetry, vertical_symmetry)
            return self.symmetry

        except Exception as e:
            logger.exception(f'Exception: {e}. \nFailed measuring symmetry')

    def measure_vertical_symmetry(self):
        """
        Measure the vertical symmetry of the robot.
        """
        try:
            coordinates = self.collect_all_coordinates()

            vertical_mirrored = 0
            vertical_total = 0
            # Calculate vertical symmetry in body
            for position in coordinates:
                if position[2] != 0:
                    vertical_total += 1
                    if (position[0], position[1], -position[2]) in coordinates:
                        vertical_mirrored += 1

            vertical_symmetry = vertical_mirrored / vertical_total if vertical_mirrored > 0 else 0

            self.symmetry_vertical = vertical_symmetry
            return self.symmetry_vertical

        except Exception as e:
            logger.exception(f'Exception: {e}. \nFailed measuring vertical symmetry')

    def measure_coverage(self):
        """
        Measure the coverage of the robot, specified by the amount of modules
        divided by the spanning surface of the robot (excluding sensors)
        :return:
        """
        if self.absolute_size is None:
            self.measure_absolute_size()
        if self.width is None or self.height is None or self.z_depth is None:
            self.measure_width_height_zdepth()
        if self.width * self.height * self.z_depth != 0:
            self.coverage = self.absolute_size / (self.width * self.height * self.z_depth)
        else:
            self.coverage = 0
        return self.coverage

    def find_bottom_layer(self):
        if self.bottom_layer is None:
            self.bottom_layer = self._find_bottom_layer(self.body)

        return self.bottom_layer

    def _find_bottom_layer(self, module, _bottom_layer=0):
        my_bottom_layer = module.substrate_coordinates[2]
        if my_bottom_layer < _bottom_layer:
            _bottom_layer = my_bottom_layer
        if module.has_children():
            for _slot, child_module in module.iter_children():
                if child_module is None:
                    continue
                child_bottom_layer = self._find_bottom_layer(child_module)
                if child_bottom_layer < _bottom_layer:
                    _bottom_layer = child_bottom_layer
        return _bottom_layer

    def measure_base_density(self):
        """
        Measure the coverage of the robot, specified by the amount of modules
        divided by the spanning surface of the robot (excluding sensors)
        :return:
        """
        bottom_layer = self.find_bottom_layer()

        hinges, bricks, _brick_sensors, _touch_sensors \
            = self.count_blocks(_filter=lambda module: module.substrate_coordinates[2] != bottom_layer)

        size_first_layer = hinges + bricks

        if self.width is None or self.height is None or self.z_depth is None:
            self.measure_width_height_zdepth()

        self.base_density = size_first_layer / (self.width * self.height)
        return self.base_density

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
                for _slot, child_module in module.iter_children():
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
        Measure proportion, specified by the 2d ratio of the body
        :return:
        """
        if self.width is None or self.height is None:
            self.measure_width_height_zdepth()
        if self.width < self.height:
            self.proportion = self.width / self.height
        else:
            if self.width != 0:
                self.proportion = self.height / self.width
        return self.proportion

    def measure_height_base_ratio(self):
        """
        Provides a ratio of the height divided by the length of the side of a square with equivalent area to the base.
        """

        if self.width is None or self.height is None or self.z_depth is None:
            self.measure_width_height_zdepth()
        if self.width * self.height != 0:
            self.height_base_ratio = self.z_depth / math.sqrt(self.width * self.height)
        else:
            self.height_base_ratio = 0
        return self.height_base_ratio

    def count_free_slots(self, module=None, init=True):
        """
        Count amount of free slots in body
        """
        if module is None:
            module = self.body
        if init:
            self.free_slots = 0
        children_count = 0
        for _slot, child_module in module.iter_children():
            if child_module is None:
                continue
            if not isinstance(child_module, TouchSensorModule):
                children_count += 1
            self.count_free_slots(child_module, False)
        if isinstance(module, CoreModule):
            self.free_slots += (4 - children_count)
        if isinstance(module, BrickModule):
            self.free_slots += (3 - children_count)

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

    def calculate_count(self):
        """
        Count amount of modules for each distinct type
        """
        try:
            self.hinge_count = 0
            self.brick_count = 0
            self.brick_sensor_count = 0
            self.touch_sensor_count = 0

            _hinge_count, _brick_count, _brick_sensor_count, _touch_sensor_count \
                = self.count_blocks()

            self.hinge_count = _hinge_count
            self.brick_count = _brick_count
            self.brick_sensor_count = _brick_sensor_count
            self.touch_sensor_count = _touch_sensor_count

        except Exception as e:
            logger.exception(f'Exception: {e}. \nFailed calculating count')

    def count_blocks(self,
                     module=None,
                     _filter=lambda module: False):
        """
        Count amount of modules for each distinct type
        """
        hinge_count = 0
        brick_count = 0
        brick_sensor_count = 0
        touch_sensor_count = 0

        if module is None:
            module = self.body
        elif isinstance(module, ActiveHingeModule) and not _filter(module):
            hinge_count += 1
        elif isinstance(module, BrickModule) and not _filter(module):
            brick_count += 1
        elif isinstance(module, BrickSensorModule) and not _filter(module):
            brick_sensor_count += 1
        elif isinstance(module, TouchSensorModule) and not _filter(module):
            touch_sensor_count += 1
        elif isinstance(module, CoreModule):
            raise RuntimeError("Core module should never be passed in")

        if module.has_children():
            for _slot, child_module in module.iter_children():
                if child_module is None:
                    continue
                _hinge_count, _brick_count, _brick_sensor_count, _touch_sensor_count \
                    = self.count_blocks(child_module, _filter)
                hinge_count += _hinge_count
                brick_count += _brick_count
                brick_sensor_count += _brick_sensor_count
                touch_sensor_count += _touch_sensor_count

        return hinge_count, brick_count, brick_sensor_count, touch_sensor_count

    def measure_width_height_zdepth(self):
        """
        Measure width and height of body, excluding sensors
        """
        try:
            coordinates = self.collect_all_coordinates()
            self.width = 0
            self.height = 0
            self.z_depth = 0
            min_x = 0
            max_x = 0
            min_y = 0
            max_y = 0
            min_z = 0
            max_z = 0

            for coordinate in coordinates:
                min_x = coordinate[0] if coordinate[0] < min_x else min_x
                max_x = coordinate[0] if coordinate[0] > max_x else max_x
                min_y = coordinate[1] if coordinate[1] < min_y else min_y
                max_y = coordinate[1] if coordinate[1] > max_y else max_y
                min_z = coordinate[2] if coordinate[2] < min_z else min_z
                max_z = coordinate[2] if coordinate[2] > max_z else max_z

            self.width = abs(min_x - max_x) + 1
            self.height = abs(min_y - max_y) + 1
            self.z_depth = abs(min_z - max_z) + 1
        except Exception as e:
            logger.exception(f'Exception: {e}. \nFailed measuring width, height and length')

    def measure_all(self):
        """
        Perform all measurements
        :return:
        """
        self.measure_limbs()
        self.measure_length_of_limbs()
        self.measure_width_height_zdepth()
        self.measure_absolute_size()
        self.measure_proportion()
        self.measure_joints()
        self.measure_coverage()
        self.measure_symmetry()
        self.measure_vertical_symmetry()
        self.measure_branching()
        self.measure_sensors()
        self.measure_height_base_ratio()
        self.measure_base_density()
        self.find_bottom_layer()
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
            'z_depth': self.z_depth,
            'absolute_size': self.absolute_size,
            'sensors': self.sensors,
            'symmetry': self.symmetry,
            'vertical_symmetry': self.symmetry_vertical,
            'height_base_ratio': self.height_base_ratio,
            'base_density': self.base_density,
            'bottom_layer': self.bottom_layer,
        }

    def __repr__(self):
        return self.measurements_to_dict().__repr__()
