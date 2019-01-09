from .element import Element
from .posable import Posable

class Inertial(Posable):
    """
    Children:
    - [opt] Mass
    - [opt] Inertia
    - [opt] Frame
    - [opt] Pose
    """
    TAG_NAME = "inertial"

class Mass(Element):
    TAG_NAME = "mass"
    def __init__(self, value: float):
        body = "{}".format(value)
        super().__init__(body=body)

class Inertia(Element):
    TAG_NAME = "inertia"
    def __init__(self, ixx=1.0, ixy=0.0, ixz=0.0, iyy=1.0, iyz=0.0, izz=1.0):
        raise NotImplementedError() #TODO http://sdformat.org/spec?ver=1.6&elem=link
