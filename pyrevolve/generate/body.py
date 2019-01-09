"""
Body generation utilities,
"""
from __future__ import absolute_import

import random
from pyrevolve.spec import BodyImplementation
from pyrevolve.spec import PartSpec
from pyrevolve.spec import BodyPart

from pyrevolve.spec.msgs import Body


def _init_part_list(spec, parts):
    specs = {part_type: spec.get(part_type) for part_type in parts}
    none_values = [k for k in specs if specs[k] is None]
    if none_values:
        raise ValueError("Invalid body part(s): {}"
                         .format(', '.join(none_values)))

    return specs


class BodyGenerator(object):
    """
    Generates a randomized robot body from
    a spec implementation and some configuration.

    This works as follows:
    - A number is chosen between 1 and `max_parts` to determine an upper
      limit on the number of body parts (other constraints might come into
      play first).
    - A part is chosen out of the list of available root parts to be used
      as the root. This is added to a list of parts to which an item can
      be attached
    """

    def __init__(
            self,
            spec,
            root_parts=None,
            attach_parts=None,
            min_parts=1,
            max_parts=50,
            fix_num_parts=False,
            max_inputs=None,
            max_outputs=None
    ):
        """

        :param min_parts: Minimum number of parts in each robot
        :type min_parts: int
        :param fix_num_parts:
        :type fix_num_parts: If true, fixes the number of parts to
                         `max_parts` rather than picking a random value (the
                         number of parts might still be lower if other
                         constraints apply).
        :param spec: The body implementation spec
        :type spec: BodyImplementation
        :param root_parts: A list of part specifiers that are allowed as root
                           parts, or `None` if all parts can be used as such.
        :type root_parts: list
        :param attach_parts: A list of part specifiers that are allowed as
                             non-root (i.e. attached) parts, or `None` if all
                             parts can be used.
        :type attach_parts: list
        :param max_parts: The maximum number of parts to be used in a robot;
                          must be specified for the generation to ever halt.
        :type max_parts: int
        :param max_inputs: The total maximum number of inputs.
        :type max_inputs: int
        :param max_outputs: The total maximum number of outputs.
        :type max_outputs: int
        :return:
        """
        self.min_parts = min_parts
        self.fix_parts = fix_num_parts
        self.spec = spec
        self.root_parts = root_parts if root_parts is not None \
            else spec.get_all_types()
        self.attach_parts = attach_parts if attach_parts is not None \
            else spec.get_all_types()

        # Get the part specifications, check if they are valid
        self.root_specs = _init_part_list(self.spec, self.root_parts)
        self.attach_specs = _init_part_list(self.spec, self.attach_parts)

        self.max_parts = max_parts
        self.max_inputs = max_inputs
        self.max_outputs = max_outputs
        self.label_counter = 0

    def generate(self):
        """
        Generates a robot body
        :return: The robot body
        :rtype: Body
        """
        body = Body()
        root_specs, attach_specs = self.root_specs, self.attach_specs

        # First, pick a number of body parts (this will be an upper limit)
        max_parts = self.max_parts if self.fix_parts \
            else self.choose_max_parts()

        root_part_type = self.choose_part(
                parts=self.root_parts,
                parent=None,
                body=None,
                root=True)
        root_part = root_specs[root_part_type]
        body.root.id = "bodygen-root"
        body.root.type = root_part_type
        self.initialize_part(
                spec=root_part,
                new_part=body.root,
                parent_part=None,
                root_part=body.root,
                root=True)

        # A body part counter
        counter = 1

        # Current number of inputs / outputs
        inputs = root_part.inputs
        outputs = root_part.outputs

        # List of (body part, slot) tuples for free part slots
        free = [(body.root, i) for i in range(root_part.arity)]

        attempts = 0
        while attempts < 5:
            if counter >= max_parts or not free:
                break

            # Construct a list of parts we can use that
            # would not break the constraints
            usable = self.get_allowed_parts(
                    attach_specs=attach_specs,
                    num_parts=counter,
                    inputs=inputs,
                    outputs=outputs,
                    root_part=body.root)

            if not usable:
                break

            # Pick a free parent / slot
            combination = self.choose_attachment(free, body.root)
            free.remove(combination)
            parent, slot = combination

            # Pick a new body part and target slot
            new_part_type = self.choose_part(usable, parent, body.root)
            if not new_part_type:
                attempts += 1
                continue

            new_part = attach_specs[new_part_type]
            target_slot = self.choose_target_slot(new_part, parent, body.root)

            if target_slot is False:
                attempts += 1
                continue

            conn = parent.child.add()
            conn.src = slot
            conn.dst = target_slot
            conn.part.id = "bodygen-{}".format(counter)
            conn.part.type = new_part_type
            self.initialize_part(new_part, conn.part, parent, body.root)

            # Update counters and free list
            inputs += new_part.inputs
            outputs += new_part.outputs
            counter += 1
            free += [
                (conn.part, i) for i in range(new_part.arity) if i != target_slot
            ]

        return body

    def get_allowed_parts(
            self,
            attach_specs,
            num_parts,
            inputs,
            outputs,
            root_part
    ):
        """
        Overridable function that creates a list of allowed parts for a specific
        stage of robot generation.
        :param attach_specs: Map of part identifiers to `PartSpec`s
        :param num_parts: Current number of parts
        :param inputs: Current number of inputs
        :param outputs: Current number of outputs
        :param root_part: The current body root part
        :return: List of identifiers of parts that when added do not violate
                 some robot rules,
                 By default, this checks for maximum inputs / outputs.
        :rtype: list[str]
        """
        return [item for item in attach_specs if (
            inputs + attach_specs[item].inputs <= self.max_inputs and
            outputs + attach_specs[item].outputs <= self.max_outputs
        )]

    def initialize_part(
            self,
            spec,
            new_part,
            parent_part,
            root_part,
            root=False
    ):
        """
        :param spec:
        :type spec: PartSpec
        :param new_part:
        :type new_part: BodyPart
        :param parent_part: The parent of the new part
        :param root_part: The current body root part
        :param root:
        :return:
        """
        # Initialize random parameters
        spec.set_parameters(new_part.param, spec.get_random_parameters())

        # Set random orientation in degrees
        new_part.orientation = self.choose_orientation(
                new_part=new_part,
                parent_part=parent_part,
                root_part=root_part,
                root=root)
        new_part.label = "part-{}".format(self.get_label_counter())
        return new_part

    def get_label_counter(self):
        """
        Simple incremental counter for part labels.
        :return:
        """
        self.label_counter += 1
        return self.label_counter

    def choose_orientation(self, new_part, parent_part, root_part, root=False):
        """
        Overridable method to choose the degrees of orientation of the
        new part.
        :param new_part:
        :type new_part: BodyPart
        :param parent_part:
        :param root_part: The current robot body root part
        :param root: Whether the given part is the root part.
        :type root: bool
        :return: Degrees of orientation
        :rtype: float
        """
        return random.uniform(0, 360)

    def choose_part(self, parts, parent_part, root_part, root=False):
        """
        Overridable method to choose a body part from a list
        of part type identifiers. This method may return
        false to indicate that no suitable part is available
        to be chosen for the given parent.
        :param parts: List of part types that are currently possible
                      within robot constraints.
        :type parts: list[str]
        :param parent_part: Parent body part
        :param root_part: The robot body
        :param root: Whether the part is root
        :return: The chosen part or `False`
        :rtype: str|bool
        """
        return random.choice(parts)

    @staticmethod
    def choose_attachment(
            attachments,
            root_part
    ):
        """
        Overridable method to choose a parent/slot combination
        from a list of attachments.
        :param attachments:
        :param root_part: The current root of the tree with connections,
                          for inspection
        :return: The chosen parent / slot tuple
        :rtype: tuple
        """
        return random.choice(attachments)

    @staticmethod
    def choose_target_slot(
            new_part,
            parent,
            root_part
    ):
        """
        Overridable method to choose a target attachment
        slot for a new part.
        :param new_part:
        :type new_part: PartSpec
        :param parent: Part parent
        :param root_part: Current robot body root
        :return:
        """
        return random.randint(0, new_part.arity - 1)

    def choose_max_parts(self):
        """
        Overridable method to pick the part limit for
        the robot to be generated.
        :return:
        """
        return random.randint(self.min_parts, self.max_parts)


class FixedOrientationBodyGenerator(BodyGenerator):
    """
    Convenience body generator that supports only a  limited number of
    orientations. By default, increments of 90 degrees are used. This
    type of custom generator is trivial to create, this class serves
    also as a simple example on how to to such a thing.
    """
    ORIENTATIONS = [0, 90, 180, 270]

    def choose_orientation(self, new_part, parent_part, root_part, root=False):
        """
        :param parent_part:
        :param root_part:
        :param new_part:
        :param root:
        :return:
        """
        return random.choice(self.ORIENTATIONS)
