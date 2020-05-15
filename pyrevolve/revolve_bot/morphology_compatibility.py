from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Optional
    from pyrevolve.evolution.individual import Individual


class MorphologyCompatibility:
    def __init__(self,
                 total_threshold: float = 1.0,
                 branching_modules_count: float = 0.0,
                 branching: float = 0.0,
                 extremities: float = 0.0,
                 limbs: float = 0.0,
                 extensiveness: float = 0.0,
                 length_of_limbs: float = 0.0,
                 coverage: float = 0.0,
                 joints: float = 0.0,
                 active_hinges_count: float = 0.0,
                 proportion: float = 0.0,
                 width: float = 0.0,
                 height: float = 0.0,
                 z_depth: float = 0.0,
                 absolute_size: float = 0.0,
                 size: float = 0.0,
                 sensors: float = 0.0,
                 symmetry: float = 0.0,
                 hinge_count: float = 0.0,
                 brick_count: float = 0.0,
                 brick_count_proportion: float = 0.0,
                 brick_sensor_count: float = 0.0,
                 touch_sensor_count: float = 0.0,
                 free_slots: float = 0.0,
                 height_base_ratio: float = 0.0,
                 max_permitted_modules: Optional[int] = None,
                 symmetry_vertical: float = 0.0,
                 base_density: float = 0.0,
                 bottom_layer: float = 0.0,
                 ):
        # Total threshold
        self.total_threshold: float = total_threshold

        # Absolute branching
        self.branching_modules_count: float = branching_modules_count
        # Relative branching
        self.branching: float = branching
        # Absolute number of limbs
        self.extremities: float = extremities
        # Relative number of limbs
        self.limbs: float = limbs
        # Absolute length of limbs
        self.extensiveness: float = extensiveness
        # Relative length of limbs
        self.length_of_limbs: float = length_of_limbs
        # Coverage
        self.coverage: float = coverage
        # Relative number of effective active joints
        self.joints: float = joints
        # Absolute number of effective active joints
        self.active_hinges_count: float = active_hinges_count
        # Proportion
        self.proportion: float = proportion
        # Width
        self.width: float = width
        # Height
        self.height: float = height
        # Z depth
        self.z_depth: float = z_depth
        # Absolute size
        self.absolute_size: float = absolute_size
        # Relative size in respect of the max body size `max_permitted_modules`
        self.size: float = size
        # Proportion of sensor vs empty slots
        self.sensors: float = sensors
        # Body symmetry in the xy plane
        self.symmetry: float = symmetry
        # Number of active joints
        self.hinge_count: float = hinge_count
        # Number of bricks
        self.brick_count: float = brick_count
        # Number of bricks proportionate to max size
        self.brick_count_proportion: float = brick_count_proportion
        # Number of brick sensors
        self.brick_sensor_count: float = brick_sensor_count
        # Number of touch sensors
        self.touch_sensor_count: float = touch_sensor_count
        # Number of free slots
        self.free_slots: float = free_slots
        # Ratio of the height over the root of the area of the base
        self.height_base_ratio: float = height_base_ratio
        # Maximum number of modules allowed (sensors excluded)
        self.max_permitted_modules: Optional[int] = max_permitted_modules
        # Vertical symmetry
        self.symmetry_vertical: float = symmetry_vertical
        # Base model density
        self.base_density: float = base_density
        # Bottom layer of the robot
        self.bottom_layer: float = bottom_layer

    def compatible_individuals(self,
                               individual1: Individual,
                               individual2: Individual) -> bool:
        morph_measure_1 = individual1.phenotype.measure_body()
        morph_measure_2 = individual2.phenotype.measure_body()
        _1 = morph_measure_1
        _2 = morph_measure_2

        # TODO consider normalization of some of these values, some are already normalized by definition

        total_distance: float = 0.0
        total_distance += self.branching_modules_count * abs(_2.branching_modules_count - _1.branching_modules_count)
        total_distance += self.branching * abs(_2.branching - _1.branching)
        total_distance += self.extremities * abs(_2.extremities - _1.extremities)
        total_distance += self.limbs * abs(_2.limbs - _1.limbs)
        total_distance += self.extensiveness * abs(_2.extensiveness - _1.extensiveness)
        total_distance += self.length_of_limbs * abs(_2.length_of_limbs - _1.length_of_limbs)
        total_distance += self.coverage * abs(_2.coverage - _1.coverage)
        total_distance += self.joints * abs(_2.joints - _1.joints)
        total_distance += self.active_hinges_count * abs(_2.active_hinges_count - _1.active_hinges_count)
        total_distance += self.proportion * abs(_2.proportion - _1.proportion)
        total_distance += self.width * abs(_2.width - _1.width)
        total_distance += self.height * abs(_2.height - _1.height)
        total_distance += self.z_depth * abs(_2.z_depth - _1.z_depth)
        total_distance += self.absolute_size * abs(_2.absolute_size - _1.absolute_size)
        if self.max_permitted_modules is not None and self.size != 0.0:
            total_distance += self.size * \
                              abs(_2.absolute_size - _1.absolute_size) / self.max_permitted_modules
        total_distance += self.sensors * abs(_2.sensors - _1.sensors)
        total_distance += self.symmetry * abs(_2.symmetry - _1.symmetry)
        total_distance += self.hinge_count * abs(_2.hinge_count - _1.hinge_count)
        total_distance += self.brick_count * abs(_2.brick_count - _1.brick_count)
        if self.max_permitted_modules is not None and self.brick_count_proportion != 0.0:
            total_distance += self.brick_count_proportion * \
                              abs(_2.brick_count - _1.brick_count) / self.max_permitted_modules
        total_distance += self.brick_sensor_count * abs(_2.brick_sensor_count - _1.brick_sensor_count)
        total_distance += self.touch_sensor_count * abs(_2.touch_sensor_count - _1.touch_sensor_count)
        total_distance += self.free_slots * abs(_2.free_slots - _1.free_slots)
        total_distance += self.height_base_ratio * abs(_2.height_base_ratio - _1.height_base_ratio)
        total_distance += self.symmetry_vertical * abs(_2.symmetry_vertical - _1.symmetry_vertical)
        total_distance += self.base_density * abs(_2.base_density - _1.base_density)
        total_distance += self.bottom_layer * abs(_2.bottom_layer - _1.bottom_layer)

        return total_distance <= self.total_threshold
