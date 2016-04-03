from __future__ import absolute_import

import random

from ....generate import FixedOrientationBodyGenerator
from ....spec import BodyImplementation, PartSpec, ParamSpec
from ..body_parts import *

# A utility function to generate color property parameters. Note that color parameters do not mutate.
channel_func = lambda channel: ParamSpec(channel, min_value=0, max_value=1, default=0.5, epsilon=0)
color_params = [channel_func("red"), channel_func("green"), channel_func("blue")]


def get_body_spec(conf):
    """
    :return:
    :rtype: BodyImplementation
    """
    parts = {
        "Core": PartSpec(
            body_part=CoreComponent,
            arity=4,
            inputs=0 if conf.disable_sensors else 6,
            params=color_params
        ),
        "FixedBrick": PartSpec(
            body_part=FixedBrick,
            arity=4,
            params=color_params
        ),
        "ActiveHinge": PartSpec(
            body_part=ActiveHinge,
            arity=2,
            outputs=1,
            params=color_params
        ),
        "Hinge": PartSpec(
            body_part=Hinge,
            arity=2,
            params=color_params
        ),
        "ParametricBarJoint": PartSpec(
            body_part=ParametricBarJoint,
            arity=2,
            params=[ParamSpec(
                "connection_length",
                default=50,
                min_value=20,
                max_value=100,
                epsilon=conf.body_mutation_epsilon
            ), ParamSpec(
                "alpha",
                default=0,
                min_value=-0.5 * math.pi,
                max_value=0.5 * math.pi,
                epsilon=conf.body_mutation_epsilon
            ), ParamSpec(
                "beta",
                default=0,
                min_value=0,
                max_value=0 if conf.enforce_planarity else math.pi,
                epsilon=conf.body_mutation_epsilon
            )] + color_params
        )
    }

    if conf.enable_wheel_parts:
        parts.update({
            "Wheel": PartSpec(
                body_part=Wheel,
                arity=1,
                params=color_params + [
                    ParamSpec("radius", min_value=40, max_value=80, default=60, epsilon=conf.body_mutation_epsilon)
                ]
            ),
            "ActiveWheel": PartSpec(
                body_part=ActiveWheel,
                arity=1,
                outputs=1,
                params=color_params + [
                    ParamSpec("radius", min_value=40, max_value=80, default=60, epsilon=conf.body_mutation_epsilon)
                ]
            ),
            "Cardan": PartSpec(
                body_part=Cardan,
                arity=2,
                params=color_params
            ),
            "ActiveCardan": PartSpec(
                body_part=ActiveCardan,
                arity=2,
                outputs=2,
                params=color_params
            ),
            "ActiveRotator": PartSpec(
                body_part=ActiveRotator,
                arity=2,
                outputs=1,
                params=color_params
            ),
            "ActiveWheg": PartSpec(
                body_part=ActiveWheg,
                arity=2,
                outputs=1,
                params=color_params + [
                    ParamSpec("radius", min_value=40, max_value=80, default=60, epsilon=conf.body_mutation_epsilon)
                ]
            )
        })

    if not conf.disable_sensors:
        if conf.enable_touch_sensor:
            parts['TouchSensor'] = PartSpec(
                body_part=TouchSensor,
                arity=1,
                inputs=2,
                params=color_params
            )

        if conf.enable_light_sensor:
            parts['LightSensor'] = PartSpec(
                body_part=LightSensor,
                arity=1,
                inputs=1,
                params=color_params
            )

    return BodyImplementation(parts)


class BodyGenerator(FixedOrientationBodyGenerator):
    """
    Body generator for ToL with some additions
    """

    def __init__(self, conf):
        """
        """
        body_spec = get_body_spec(conf)
        self.conf = conf
        super(BodyGenerator, self).__init__(
            body_spec,

            # Only "Core" can serve as a root node
            root_parts=["Core"],

            # All other parts can potentially be attached
            attach_parts=[part_type for part_type in body_spec.get_all_types()
                          if part_type != "Core"],

            # Require at least some complexity
            min_parts=conf.min_parts,

            # High number of maximum parts, limit will probably be something else
            max_parts=conf.max_parts,

            # Maximum number of sensory inputs
            max_inputs=conf.max_inputs,

            # Maximum number of motor outputs
            max_outputs=conf.max_outputs
        )
        self.last_parameters = None

    def initialize_part(self, spec, new_part, parent_part, root_part, root=False):
        """
        Overrides `initialize_part` to make sure all parts get
        the same color as the root part
        :param parent_part:
        :param spec:
        :param new_part:
        :param root_part:
        :param root:
        """
        params = spec.get_random_parameters(serialize=False)
        if root:
            self.last_parameters = params
        elif self.last_parameters:
            params['red'], params['green'], params['blue'] = \
                self.last_parameters['red'], self.last_parameters['green'], self.last_parameters['blue']

        new_part.orientation = self.choose_orientation(new_part, parent_part, root_part, root)
        spec.set_parameters(new_part.param, params)
        return new_part

    def generate(self):
        """
        Resets `last_parameters` so that body parts built by the mutator
        will get random colors still.
        """
        result = super(BodyGenerator, self).generate()
        self.last_parameters = None
        return result

    def choose_part(self, parts, parent, body, root=False):
        """
        Overridable method to choose a body part from a list
        of part type identifiers.
        :param parts:
        :type parts: list[str]
        :param parent: Parent body part
        :param body: The robot body
        :param root: Whether the part is root
        :return: The chosen part
        :rtype: str
        """
        # Don't chain parametric bar joints, it leads to ugly constructions
        if parent and parent.type == "ParametricBarJoint":
            parts = [p for p in parts if p != "ParametricBarJoint"]

        return False if not parts else random.choice(parts)
