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

class Mesh(Element):
    """
    Children:
    - [1] URI
    - [opt] Submesh
    - [opt] Scale
    """
    TAG_NAME = "mesh"
    def __init__(self, uri: str, scale=None):
        elements = [
            URI(text=uri)
        ]
        if scale is not None:
            elements.append(_Scale(scale.x, scale.y, scale.z))
        super().__init__(elements=elements)

class URI(Element):
    TAG_NAME = "uri"
    def __init__(self, text: str):
        super().__init__(body=text)

class SubMesh(Element):
    """
    Children:
    - [1] Name
    - [0] Center
    """
    TAG_NAME = "submesh"
    def __init__(self):
        raise NotImplementedError()

class _Scale(Element):
    TAG_NAME = "scale"
    def __init__(self, x:float, y:float, z:float):
        super().__init__(body="{} {} {}".format(x,y,z))
    