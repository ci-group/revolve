from .pose import Pose, Posable
from .link import Link, BoxLink, Inertial
from .geometry import Visual, Collision, MeshGeometry, BoxGeometry

import xml.etree.ElementTree


def sub_element_text(parent, name, text):
    el = xml.etree.ElementTree.SubElement(parent, name)
    if type(text) is float or type(text) is int:
        el.text = '{:e}'.format(text)
    else:
        el.text = str(text)
    return el
