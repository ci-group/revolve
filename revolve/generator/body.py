"""
Body generation utilities,
"""
import random
from ..spec import BodyImplementation, PartSpec, BodyPart
from ..spec.protobuf import Body


class BodyGenerator(object):
    """
    generates a randomized robot body from
    a spec implementation and some configuration.

    This works as follows:
    - A number is chosen between 1 and `max_parts` to determine an upper
      limit on the number of body parts (other constraints might come into
      play first).
    - A part is chosen out of the list of available root parts to be used
      as the root. This is added to a list of parts to which an item can
      be attached
    """

    def __init__(self, spec, root_parts=None, attach_parts=None, max_parts=50,
                 max_inputs=None, max_outputs=None):
        """

        :param spec: The body implementation spec
        :type spec: BodyImplementation
        :param root_parts: A list of part specifiers that are allowed as root parts,
                          or `None` if all parts can be used as such.
        :type root_parts: list
        :param attach_parts: A list of part specifiers that are allowed as non-root (i.e. attached) parts,
                             or `None` if all parts can be used.
        :type attach_parts: list
        :param max_parts: The maximum number of parts to be used in a robot; must be specified for
                          the generation to ever halt.
        :type max_parts: int
        :param max_inputs: The total maximum number of inputs.
        :type max_inputs: int
        :param max_outputs: The total maximum number of outputs.
        :type max_outputs: int
        :return:
        """
        self.spec = spec
        self.root_parts = root_parts if root_parts is not None else spec.get_all_types()
        self.attach_parts = attach_parts if attach_parts is not None else spec.get_all_types()

        self.max_parts = max_parts
        self.max_inputs = max_inputs
        self.max_outputs = max_outputs

    def generate(self):
        """
        Generates a robot body
        """
        body = Body()

        # First, pick a number of body parts (this will be an upper limit)
        max_parts = self.choose_max_parts()

        # Get the part specifications, check if they are valid
        root_specs = [self.spec.get(part_type) for part_type in self.root_parts]
        attach_specs = [self.spec.get(part_type) for part_type in self.attach_parts]

        if None in root_specs:
            raise ValueError("Identifier '%s' is not a valid root body part."
                             % self.root_parts[root_specs.index(None)])

        if None in attach_specs:
            raise ValueError("Identifier '%s' is not a valid attach body part."
                             % self.attach_parts[attach_specs.index(None)])

        root_part = self.choose_part(root_specs, True)
        body.root.id = "bodygen-root"
        self.initialize_part(root_part, body.root, root=True)

        # A body part counter
        counter = 0

        # Current number of inputs / outputs
        inputs = root_part.inputs
        outputs = root_part.outputs

        # List of (body part, slot) tuples for free part slots
        free = set([(body.root, i) for i in range(root_part.arity)])

        while True:
            if counter >= max_parts or not free:
                break

            # Construct a list of parts we can use that
            # would not break the constraints
            usable = [item for item in attach_specs if (
                inputs + item.inputs <= self.max_inputs and
                outputs + item.outputs <= self.max_outputs
            )]

            if not usable:
                break

            # Pick a free slot
            combination = random.choice(free)
            free.remove(combination)
            parent, slot = combination

            # Pick a new body part and target slot
            new_part = self.choose_part(usable)
            target_slot = self.choose_target_slot(new_part)

            conn = parent.child.add()
            conn.src = slot
            conn.dst = target_slot
            conn.part.id = "bodygen-%d" % counter
            self.initialize_part(new_part, conn.part)

            # Update counters and free list
            inputs += new_part.inputs
            outputs += new_part.outputs
            counter += 1
            free.update([(conn.part, i) for i in range(new_part.arity) if i != target_slot])

        return body

    def initialize_part(self, spec, part, root=False):
        """
        :param spec:
        :type spec: PartSpec
        :param part:
        :type part: BodyPart
        :return:
        """
        # Initialize random parameters
        for p in spec.parameters:
            new_param = part.param.add()
            new_param.value = p.get_random_value()

        # Set random orientation in degrees
        part.orientation = random.uniform(0, 360)
        return part

    def choose_part(self, parts, root=False):
        """
        Overridable method to choose a body part from a list
        of parts.
        :param parts:
        :param root:
        :return: The chosen part
        :rtype: PartSpec
        """
        return random.choice(parts)

    def choose_attachment(self, attachments):
        """
        Overridable method to choose a parent/slot combination
        from a list of attachments.
        :param attachments:
        :return: The chosen parent / slot tuple
        :rtype: tuple
        """
        return random.choice(attachments)

    def choose_target_slot(self, new_part):
        """
        Overridable method to choose a target attachment
        slot for a new part.
        :param new_part:
        :type new_part: PartSpec
        :return:
        """
        return random.randint(0, new_part.arity - 1)

    def choose_max_parts(self):
        """
        Overridable method to pick the part limit for
        the robot to be generated.
        :return:
        """
        return random.randint(1, self.max_parts)
