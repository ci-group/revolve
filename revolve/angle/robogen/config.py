from __future__ import absolute_import


class Config:
    def __init__(self,
                 min_parts,
                 max_parts,
                 max_inputs,
                 max_outputs,
                 body_mutation_epsilon=0.05,
                 enforce_planarity=True,
                 disable_sensors=False,
                 enable_touch_sensor=True,
                 enable_light_sensor=False,
                 enable_wheel_parts=False):
        self.max_inputs = max_inputs
        self.max_outputs = max_outputs
        self.body_mutation_epsilon = body_mutation_epsilon
        self.enforce_planarity = enforce_planarity
        self.disable_sensors = disable_sensors
        self.enable_touch_sensor = enable_touch_sensor
        self.enable_light_sensor = enable_light_sensor
        self.enable_wheel_parts = enable_wheel_parts
        self.max_parts = max_parts
        self.min_parts = min_parts
