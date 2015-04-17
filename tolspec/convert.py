from __future__ import print_function
import sys
from .tol_pb2 import *
import re


class LinesToProtobuf:
    """

    """
    # Match (optional whitespace)(hash)(anything)
    COMMENT_REGEX = re.compile(r"^\s*#.*$")

    # Empty line is just whitespace
    EMPTY_REGEX = re.compile(r"^\s*$")

    # match (0 or more tabs)(slot) (type) (id) (orientation) (parameters)(ignore whitespace)
    PART_REGEX = re.compile(r"^(\t*)(\d) ([A-Za-z]+) ([^\s]+) (\d)( [-+]?[0-9]*\.?[0-9]+)*(?:\s+)$")

    # Regex for hidden neurons
    NEURON_REGEX = re.compile(r"^([^\s]+) ([^\s]+)$")

    def __init__(self, lines):
        """
        :param lines: Iterable with file lines
        """
        self.lines = lines
        self.robot = Robot()
        self.robot.body = Body()
        self.robot.brain = Brain()
        self.parent_stack = []
        self.part_ids = set()

    def get_protobuf(self, robot_id=0):
        """
        Takes an iterator of file lines, and turns it into a Protobuf
        robot specification.
        :param robot_id: ID to set on the resulting robot (defaults to zero)
        :type robot_id: int
        :return:
        """
        processors = iter([self._read_part_line, self._read_neuron_line,
                           self._read_weight_line, self._read_params_line])
        processor = next(processors)

        nr = 0
        for line in self.lines:
            nr += 1
            if self.is_comment_line(line):
                continue

            if self.is_empty_line(line):
                # Skip to the next part
                processor = next(processors, None)
                continue

            if processor is None:
                raise ValueError("Unexpected line %d: nothing more to process." % nr)

            try:
                processor(line)
            except StandardError as e:
                print("Error on line %d.", file=sys.stderr)
                raise e

        self.robot.id = robot_id
        return self.robot

    def _read_part_line(self, line):
        """

        :param line:
        :return:
        """
        matches = self.PART_REGEX.match(line)
        if not matches:
            raise ValueError("Invalid part line format.")

        indent = len(matches.group(1))
        root = (indent == 0)
        slot = int(matches.group(2))

        while indent < len(self.parent_stack):
            self.parent_stack.pop()

        if root:
            if slot != 0:
                raise ValueError("Slot of root node should be '0'.")

            part = self.robot.body.root = BodyPart()
        else:
            parent = self.parent_stack[-1]
            conn = parent.children.add()
            part = conn.part = BodyPart()

            # Set connection properties; destination slot is currently
            # not configurable in file and always zero!
            conn.srcSlot = slot
            conn.destSlot = 0

        # Add other part properties
        part.type = matches.group(3)
        part.id = matches.group(4)
        part.orientation = int(matches.group(5))

        if root and self.robot.HasField("root"):
            raise ValueError("More than one root node.")

        if part.id in self.part_ids:
            raise ValueError("Duplicate part ID: %s" % part.id)

        self.part_ids.add(part.id)

        # Add parameters
        params = matches.group(6)
        if len(params):
            for raw in re.split(r"\s+", params):
                param = part.evolvableParam.add()
                param.paramValue = float(raw)

        if indent > len(self.parent_stack):
            if (indent - len(self.parent_stack)) > 1:
                raise ValueError("Indentation error.")

            self.parent_stack.append(part)

    def _read_neuron_line(self, line):
        """
        :param line:
        :return:
        """
        matches = self.NEURON_REGEX.match(line)
        if not matches:
            raise ValueError("Cannot read neuron line.")

        self.part_ids.add()

    def _read_weight_line(self, line):
        """

        :param line:
        :return:
        """

    def _read_params_line(self, line):
        """

        :param line:
        :return:
        """

    def is_comment_line(self, line):
        """
        :param line:
        :type line: str
        :return:
        :rtype: bool
        """
        return bool(self.COMMENT_REGEX.match(line))

    def is_empty_line(self, line):
        """

        :param line:
        :return:
        """
        return bool(self.EMPTY_REGEX.match(line))
