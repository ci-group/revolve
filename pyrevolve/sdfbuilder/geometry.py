from .element import Element

class Geometry(Element):
    TAG_NAME = "geometry"

class Sphere(Element):
    TAG_NAME = "sphere"
    def __init__(self, radius=1.0):
        radius = _Radius(radius=radius)
        super().__init__(elements=[radius])

class _Radius(Element):
    TAG_NAME = "radius"
    def __init__(self, radius: float):
        body = "{}".format(radius)
        super().__init__(body=body)
