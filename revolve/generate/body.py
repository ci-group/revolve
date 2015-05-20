"""
Body generation utilities,
"""
import random
from ..spec import BodyImplementation, PartSpec, BodyPart
from ..spec.msgs import Body


def _init_part_list(spec, parts):
    specs = {part_type: spec.get(part_type) for part_type in parts}
    none_values = [k for k in specs if specs[k] is None]
    if none_values:
        raise ValueError("Invalid body part(s): %s"
                         % ', '.join(none_values))

    return specs


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
                 fix_num_parts=False, max_inputs=None, max_outputs=None):
        """

        :param fix_num_parts:
        :type fix_num_parts: If true, fixes the number of parts to `max_parts` rather than
                         picking a random value (the number of parts might still be lower
                         if other constraints apply).
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
        self.fix_parts = fix_num_parts
        self.spec = spec
        self.root_parts = root_parts if root_parts is not None else spec.get_all_types()
        self.attach_parts = attach_parts if attach_parts is not None else spec.get_all_types()

        # Get the part specifications, check if they are valid
        self.root_specs = _init_part_list(self.spec, self.root_parts)
        self.attach_specs = _init_part_list(self.spec, self.attach_parts)

        self.max_parts = max_parts
        self.max_inputs = max_inputs
        self.max_outputs = max_outputs

    def generate(self):
        """
        Generates a robot body
        :return: The robot body
        :rtype: Body
        """
        body = Body()
        root_specs, attach_specs = self.root_specs, self.attach_specs

        # First, pick a number of body parts (this will be an upper limit)
        max_parts = self.max_parts if self.fix_parts else self.choose_max_parts()

        root_part_type = self.choose_part(self.root_parts, True)
        root_part = root_specs[root_part_type]
        body.root.id = "bodygen-root"
        body.root.type = root_part_type
        self.initialize_part(root_part, body.root, root=True)

        # A body part counter
        counter = 1

        # Current number of inputs / outputs
        inputs = root_part.inputs
        outputs = root_part.outputs

        # List of (body part, slot) tuples for free part slots
        free = [(body.root, i) for i in range(root_part.arity)]

        while True:
            if counter >= max_parts or not free:
                break

            # Construct a list of parts we can use that
            # would not break the constraints
            usable = self.get_allowed_parts(attach_specs, counter, inputs, outputs)

            if not usable:
                break

            # Pick a free parent / slot
            combination = self.choose_attachment(free)
            free.remove(combination)
            parent, slot = combination

            # Pick a new body part and target slot
            new_part_type = self.choose_part(usable)
            new_part = attach_specs[new_part_type]
            target_slot = self.choose_target_slot(new_part)

            conn = parent.child.add()
            conn.src = slot
            conn.dst = target_slot
            conn.part.id = "bodygen-%d" % counter
            conn.part.type = new_part_type
            self.initialize_part(new_part, conn.part)

            # Update counters and free list
            inputs += new_part.inputs
            outputs += new_part.outputs
            counter += 1
            free += [(conn.part, i) for i in range(new_part.arity) if i != target_slot]

        return body

    def get_allowed_parts(self, attach_specs, num_parts, inputs, outputs):
        """
        Overridable function that creates a list of allowed parts for a specific
        stage of robot generation.
        :param attach_specs: Map of part identifiers to `PartSpec`s
        :param num_parts: Current number of parts
        :param inputs: Current number of inputs
        :param outputs: Current number of outputs
        :return: List of identifiers of parts that when added do not violate some robot rules.
                 By default, this checks for maximum inputs / outputs.
        :rtype: list
        """
        return [item for item in attach_specs if (
            inputs + attach_specs[item].inputs <= self.max_inputs and
            outputs + attach_specs[item].outputs <= self.max_outputs
        )]

    def initialize_part(self, spec, part, root=False):
        """
        :param spec:
        :type spec: PartSpec
        :param part:
        :type part: BodyPart
        :return:
        """
        # Initialize random parameters
        for p in spec.get_random_parameters(serialize=True):
            new_param = part.param.add()
            new_param.value = p

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
