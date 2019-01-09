from sdfbuilder import SDF, Model, Link, PosableGroup
from sdfbuilder.structure import Box, Cylinder, Collision, Visual, StructureCombination
from sdfbuilder.math import Vector3
from sdfbuilder.joint import Joint
import math

# Create a box geometry
box_geom = Box(1.0, 1.0, 1.0, mass=0.5)

# Create a collision and a visual element using this box geometry
# A collision / visual's pose is determined by its geometry, so
# never use the same geometry object twice or you will get weird
# behavior when rotating.
box_col = Collision("box_collision", box_geom)
box_vis = Visual("box_visual", box_geom.copy())

# Add the two to a PosableGroup, so we can conveniently move them
# around together.
box = PosableGroup(elements=[box_col, box_vis])

# Now create a Cylinder visual/collision combi. You didn't think that the above would
# be the easiest way to do it now did you? The above was just to show you
# how that works.
cyl_geom = Cylinder(radius=0.25, length=0.5, mass=0.1)
cylinder = StructureCombination("cylinder", cyl_geom)

# Align the cylinder such that...
cylinder.align(
    # .. its bottom ..
    Vector3(0, 0, -0.5 * cyl_geom.length),

    # .. and normal vector ..
    Vector3(0, 0, -1),

    # .. under rotation of the tangent vector ..
    Vector3(0, 1, 0),

    # .. align with the top ..
    Vector3(0, 0, 0.5 * box_geom.size[2]),

    # .. and normal vector (other direction) ..
    Vector3(0, 0, 1),

    # .. rotation of the tangent vector ..
    Vector3(0, 1, 0),

    # .. of the box.
    box
)

# Now, create a link and add both items to it
link = Link("my_link", elements=[box, cylinder])

# Calculate the correct inertial properties given
# the collision elements.
link.align_center_of_mass()
link.calculate_inertial()

# Rotate the link 45 degrees around the x-axis, specified in the parent frame
# just to demonstrate how that works (and to demonstrate align is still
# going to work after the rotation).
link.rotate_around(Vector3(1, 0, 0), math.radians(45), relative_to_child=False)

# Okay, not sure what this is supposed to be, but let's another wheel-like cylinder in
# a new link, and connect them with joints
wheel_geom = Cylinder(0.75, 0.1, mass=0.1)
wheel = StructureCombination("wheel", wheel_geom)
wheel_link = Link("my_wheel", elements=[wheel])

attachment_point = Vector3(0, 0, 0.5 * wheel_geom.length)
wheel_link.align(attachment_point, Vector3(0, 0, 1), Vector3(0, 1, 0),
                 Vector3(0, 0, 0.5 * box_geom.size[0] + cyl_geom.length),
                 Vector3(0, 0, 1), Vector3(1, 0, 0), link)

# Create a joint link, and set its position (which is in the child frame)
joint = Joint("revolute", link, wheel_link, axis=Vector3(0, 0, 1))
joint.set_position(attachment_point)

# Create a model and a wrapping SDF element, and output
# Move the model up so it won't intersect with the ground when inserted.
model = Model("my_robot", elements=[link, wheel_link, joint])
model.set_position(Vector3(0, 0, math.sqrt(0.5)))
sdf = SDF(elements=[model])
print(str(sdf))
