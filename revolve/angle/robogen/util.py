from __future__ import absolute_import
from __future__ import division

from .constants import *

from sdfbuilder.physics import Friction
from sdfbuilder.structure import Collision
from sdfbuilder.util import number_format as nf
from sdfbuilder import Element


def apply_surface_parameters(model, intended_step_size=0.005):
    """
    Applies surface parameters to all collisions in the given model.
    :param model:
    :type model: Model
    :param intended_step_size:
    :return:
    """
    surface_kd = SURFACE_ERP / (SURFACE_CFM * intended_step_size)
    surface_kp = 1.0 / SURFACE_CFM - (SURFACE_ERP / SURFACE_CFM)

    # Add friction surfaces to all body parts
    surf = Element(tag_name="surface")
    friction = Friction(
        friction=SURFACE_FRICTION1,
        friction2=SURFACE_FRICTION2,
        slip1=SURFACE_SLIP1,
        slip2=SURFACE_SLIP2
    )
    contact = "<contact>" \
              "<ode>" \
              "<kd>{}</kd>" \
              "<kp>{}</kp>" \
              "</ode>" \
              "</contact>".format(
                  nf(surface_kd), nf(surface_kp)
              )

    surf.add_element(contact)
    surf.add_element(friction)

    collisions = model.get_elements_of_type(Collision, recursive=True)
    for collision in collisions:
        collision.add_element(surf)
