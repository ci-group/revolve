import xml.etree.ElementTree

from .pose import Pose, Posable
from .link import Link
from .geometry import Visual, Collision, MeshGeometry, BoxGeometry
from .inertial import Inertial
from .joint import Joint
from . import math
from .revolve_bot_sdf_builder import revolve_bot_to_sdf


def sub_element_text(parent, name, text):
    el = xml.etree.ElementTree.SubElement(parent, name)
    if type(text) is float or type(text) is int:
        el.text = '{:e}'.format(text)
    else:
        el.text = str(text)
    return el
