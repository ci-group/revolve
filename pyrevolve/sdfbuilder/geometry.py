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
    - [1] Submesh
    - [1] Scale
    """
    TAG_NAME = "mesh"
    def __init__(self, uri: str):
        super().__init__(elements=[
            URI(text=uri)
        ])

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

class Scale(Element):
    TAG_NAME = "scale"
    def __init__(self):
        raise NotImplementedError()
    