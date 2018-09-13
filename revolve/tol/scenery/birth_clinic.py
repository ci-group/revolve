from sdfbuilder import SDF, Model, Link, Element
from sdfbuilder.physics import Friction
from sdfbuilder.structure import Mesh, Visual, Collision
from sdfbuilder.math import Vector3
from sdfbuilder.util import number_format as nf

from ..config import constants

# Radius and height without scaling
MESH_DIAMETER = 4.0
MESH_HEIGHT = 4.4
SLICE_FRACTION = 0.7


class BirthClinic(Model):
    """
    Birth clinic model, consists of two cylinders, one of which is rotated.
    """

    def __init__(self, diameter=3.0, height=3.0, name="birth_clinic"):
        """

        :param diameter: Intended diameter of the birth clinic
        :param name:
        :return:
        """
        super(BirthClinic, self).__init__(name=name, static=True)

        self.diameter = diameter
        scale = diameter / MESH_DIAMETER

        # Cannot go higher than mesh height, or lower than the bottom
        # of the slice.
        scaled_height = scale * MESH_HEIGHT
        self.height = max(min(height, scaled_height), SLICE_FRACTION * scaled_height)

        mesh = Mesh("model://tol_robot/meshes/BirthClinic.dae", scale=scale)

        col = Collision("bc_col", mesh)
        surf = Element(tag_name="surface")
        friction = Friction(
            friction=0.01,
            friction2=0.01,
            slip1=1.0,
            slip2=1.0
        )
        contact = "<contact>" \
                  "<ode>" \
                  "<kd>%s</kd>" \
                  "<kp>%s</kp>" \
                  "</ode>" \
                  "</contact>" % (
                      nf(constants.SURFACE_KD), nf(constants.SURFACE_KP)
                  )
        surf.add_element(friction)
        surf.add_element(contact)
        col.add_element(surf)

        vis = Visual("bc_vis", mesh.copy())
        self.link = Link("bc_link", elements=[col, vis])

        # By default the model has 0.5 * scale * MESH_HEIGHT below
        # and above the surface. Translate such that we have exactly
        # the desired height instead.
        self.link.translate(Vector3(0, 0, self.height - (0.5 * scaled_height)))
        self.add_element(self.link)


if __name__ == '__main__':
    sdf = SDF(elements=[BirthClinic()])
    print(str(sdf))
