"""
Demonstrates creating a simple SDF bot from a spec and a YAML file.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import math
import sys
print("Actual system path is ", sys.path)

# Module imports
from pyrevolve.generate import BodyGenerator
from pyrevolve.generate import NeuralNetworkGenerator


from pyrevolve.sdfbuilder.sensor import Sensor as SdfSensor
from pyrevolve.sdfbuilder.math import Vector3
from pyrevolve.sdfbuilder import SDF, Limit
from pyrevolve.sdfbuilder.structure import Box as BoxGeom, Cylinder as CylinderGeom


from pyrevolve.spec import BodyImplementation
from pyrevolve.spec import default_neural_net
from pyrevolve.spec import PartSpec
from pyrevolve.spec import ParamSpec
from pyrevolve.spec import Robot

from pyrevolve.build.sdf.body import Box
from pyrevolve.build.sdf.body import Cylinder
from pyrevolve.build.sdf.body import ComponentJoint as Joint

from pyrevolve.build.sdf import RobotBuilder
from pyrevolve.build.sdf import BodyBuilder
from pyrevolve.build.sdf import NeuralNetBuilder
from pyrevolve.build.sdf import VelocityMotor
from pyrevolve.build.sdf import PID
from pyrevolve.build.sdf import Sensor

# Some configuration
# This is the number of times per second we will call our
# robot's brain update (in the default controller). We'll
# also use it as
UPDATE_RATE = 5


# A utility function to generate color properties
channel_func = lambda channel: ParamSpec(channel, min_value=0, max_value=1, default=0.5)
color_params = [
    channel_func("red"), channel_func("green"), channel_func("blue")
]


class ColorMixin(object):
    """
    Mixin class for "colorable" parts. Needs to be mixed
    in with a body part, or it won't work.
    """

    def apply_color(self):
        """
        Applies the "red", "green" and "blue" arguments
        to all links in this body part.
        """
        self.make_color(self.part_params["red"], self.part_params["green"], self.part_params["blue"])


# Below, we define some body parts
# The first is a simple box that serves as a root component
# We have the box include an IMU Sensor that registers the
# component's acceleration
class Core(Box, ColorMixin):
    X = 0.5
    Y = 0.8
    Z = 0.5
    MASS = 1.0

    def _initialize(self, **kwargs):
        """
        We override the default box's initialize method to
        include the color of the box.
        """
        # Don't forget to call super when a parent class actually
        # does something (Box, in this case).
        super(Core, self)._initialize(**kwargs)

        # Now we will add the IMU sensor. First, we create the
        # sensor as we would like to have it in SDF...
        imu = SdfSensor("imu_sensor", "imu", update_rate=UPDATE_RATE)

        # .. we then add this to a specific component using `add_sensor`.
        # The second argument to this function allows us to override
        # the name of the sensor handler that will be loaded. It defaults
        # to the sensor type, so specifying "imu" here has the same
        # result as leaving it empty.
        self.component.add_sensor(imu, "imu")

        # Apply generated color
        self.apply_color()


# Next, we illustrate a more complex body part, read
# the class details.
class PassiveHinge(Box, ColorMixin):
    """
    A passive joint (i.e. it can move but isn't actuated) with
    two attached blocks. One of these blocks is of fixed size,
    the other has an x-size determined by a parameter.
    """
    X = 0.5
    Y = 0.3
    Z = 0.3
    MASS = 0.1

    # Offset of the joint from the box edges
    JOINT_OFFSET = 0.1

    def _initialize(self, **kwargs):
        """
        Initialize method to generate the hinge. Inheriting from
        "box" makes sure there is a box of the given size in
        `self.link`.
        """
        super(PassiveHinge, self)._initialize(**kwargs)

        # Create the variable size block. `create_link` is the recommended
        # way of doing this, because it sets some non-default link properties
        # (such as self_collide) which you generally need.
        length = kwargs["length"]
        self.var_block = self.create_component(
                BoxGeom(length, self.y, self.z, 0.1), "var-block")

        # We move the block in the x-direction so that it
        # just about overlaps with the other block (to
        # make it seem like a somewhat realistic joint)
        self.var_block.translate(
                Vector3(0.5 * (length + self.x) - self.JOINT_OFFSET, 0, 0))

        # Now create a revolute joint at this same position. The
        # joint axis is in the y-direction.
        axis = Vector3(0, 1, 0)
        passive_joint = Joint(
                joint_type="revolute",
                parent=self.component,
                child=self.var_block,
                axis=axis)

        # Set some movement limits on the joint
        passive_joint.axis.limit = Limit(
                lower=math.radians(-45),
                upper=math.radians(45),
                effort=1.0)

        # Set the joint position - in the child frame!
        passive_joint.set_position(
                Vector3(-0.5 * length + self.JOINT_OFFSET, 0, 0))

        # Don't forget to add the joint and the link
        self.add_joint(passive_joint)

        # Apply the generated color
        self.apply_color()

    def get_slot(self, slot):
        """
        This method should return the SDF link corresponding to a
        certain slot.
        """
        # Throw a clear error if the slot doesn't exist
        self.check_slot(slot)

        # Slot 0 is the fixed box, slot 1 is the variable sized block
        return self.component if slot == 0 else self.var_block

    def get_slot_position(self, slot):
        """
        Returns the attachment position of each of the slots.
        """
        # Again, prevent errors
        self.check_slot(slot)

        # The constructor of `BodyPart` stores the initialization's kwargs
        # parameters in `self.part_params`.
        length = self.part_params["length"]

        # The center of the base box lies at (0, 0), move 1/2 x to the
        # left to get that slot, or move 1/2 x to the right, plus the
        # variable length minus the offset to get the other.
        return Vector3(-0.5 * self.x, 0, 0) if slot == 0 \
            else Vector3(0.5 * self.x + length - self.JOINT_OFFSET, 0, 0)

    def get_slot_normal(self, slot):
        """
        Return the slot normal vectors; in this case they are equal
        to the position vectors except for their length.

        Actually, it is not strictly required for normal and tangent
        vectors to be normalized, but it is good practice to do so.
        """
        return self.get_slot_position(slot).normalized()

    def get_slot_tangent(self, slot):
        """
        The tangent vectors determine the "zero orientation", meaning
        if a body part has an orientation of 0 it will have its tangent
        vector aligned with its parent. The tangent vector has to be
        orthogonal to the slot normal.

        We have no specific orientation requirements, so we simply
        always return one tangent vector which is orthogonal to both
        slot normals, i.e. the vector (0, 0, 1).
        """
        self.check_slot(slot)
        return Vector3(0, 0, 1)


# The second body part is a motorized wheel. For this, we start
# with a cylinder, and extend it to include a thin
# connecting block and a motor.
class Wheel(Cylinder, ColorMixin):
    RADIUS = 0.6
    MASS = 0.5
    LENGTH = 0.2
    MOTOR_SIZE = 0.1

    def _initialize(self, **kwargs):
        """
        :param kwargs:
        :return:
        """
        # Call super to initialize the cylinder part of the wheel
        super(Wheel, self)._initialize(**kwargs)

        # Create the small box that serves as the motor
        box_size = self.MOTOR_SIZE
        self.attachment = self.create_component(
            BoxGeom(box_size, box_size, box_size, 0.01), "cylinder-attach")

        # Get attachment position and axis of the motor joint
        anchor = Vector3(0, 0, 0.5 * self.LENGTH)
        axis = Vector3(0, 0, 1)

        # Size and position the box
        self.attachment.set_position(anchor + Vector3(0, 0, 0.5 * box_size))

        # Create revolute joint. Remember: joint position is in child frame
        motor_joint = Joint(
                joint_type="revolute",
                parent=self.component,
                child=self.attachment,
                axis=axis)
        motor_joint.set_position(Vector3(0, 0, -0.5 * box_size))

        # Set a force limit on the joint
        motor_joint.axis.limit = Limit(effort=0.01)
        self.add_joint(motor_joint)

        # Register a joint motor with a maximum velocity of
        # 50 rounds per minute (the speed is in radians per second)
        # We also give it a simple PID controller
        pid = PID(proportional_gain=1.0, integral_gain=0.1)
        max_speed = 2 * math.pi * 50.0 / 60
        self.motors.append(VelocityMotor(
                part_id=self.id,
                motor_id="rotate",
                joint=motor_joint,
                pid=pid,
                min_velocity=-max_speed,
                max_velocity=max_speed))
        self.apply_color()

    def get_slot(self, slot_id):
        """
        Override get_slot, because we should return the attachment.
        :param slot_id:
        :return:
        """
        return self.attachment

    def get_slot_position(self, slot_id):
        """
        Modify `get_slot_position` to return the attachment of the
        motor instead.
        :param slot_id:
        :return:
        """
        v = super(Wheel, self).get_slot_position(slot_id)
        return v + Vector3(0, 0, self.MOTOR_SIZE)


body_spec = BodyImplementation(
    {
        ("Core", "C"): PartSpec(
            body_part=Core,
            arity=6,
            inputs=6,
            params=color_params
        ),
        ("Wheel", "W"): PartSpec(
            body_part=Wheel,
            arity=1,
            outputs=1,

            # Add color parameters to this part
            params=color_params
        ),
        "Hinge": PartSpec(
            body_part=PassiveHinge,
            arity=2,
            params=color_params + [
                ParamSpec(
                    name="length",
                    min_value=0.1,
                    max_value=1,
                    default=0.5)
            ]
        )
    }
)

# For the brain, we use the default neural network
brain_spec = default_neural_net()

# Specify a body generator for the specification
body_gen = BodyGenerator(
    body_spec,

    # List all parts that can serve as the robot root
    root_parts=["Core"],

    # List all parts that can be attached
    attach_parts=["Wheel", "Hinge"],

    # Set the maximum number of used parts. The
    # actual number will be determined by a
    # random pick and some input / output constraints.
    max_parts=15,

    # The maximum number of input (i.e. sensory) values
    # our robot may have.
    max_inputs=8,

    # The maximum number ouf output (i.e. motory) values
    # our robot may have.
    max_outputs=12
)

# Also get a brain generator
brain_gen = NeuralNetworkGenerator(
    brain_spec,
    max_hidden=10
)

# Create a builder to convert the protobuf to SDF
builder = RobotBuilder(BodyBuilder(body_spec), NeuralNetBuilder(brain_spec))


def generate_robot(robot_id=0):
    # Create a protobuf robot
    robot = Robot()
    robot.id = robot_id

    # Generate a body
    body = body_gen.generate()
    robot.body.CopyFrom(body)

    # The neural network generator can get the interface from the body
    brain = brain_gen.generate_from_body(body, body_spec)
    robot.brain.CopyFrom(brain)

    return robot


def robot_to_sdf(robot, name="test_bot", plugin_controller=None):
    model = builder.sdf_robot(
            robot=robot,
            controller_plugin=plugin_controller,
            update_rate=UPDATE_RATE,
            name=name)
    model_sdf = SDF()
    model_sdf.add_element(model)
    return model_sdf


def generate_sdf_robot(robot_id=0, plugin_controller=None, name="test_bot"):
    robot = generate_robot(robot_id)
    return robot_to_sdf(robot, name, plugin_controller)


if __name__ == "__main__":
    # Create SDF and output
    sdf = generate_sdf_robot()
    print(str(sdf))
