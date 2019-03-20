import xml.etree.ElementTree
from pyrevolve import SDF


class Sensor(SDF.Posable):
    """
    Generic SDF sensor.

    Parent element: Link or Joint
    """
    def __init__(self, name: str, sensor_type: str, position=None, rotation=None):
        super().__init__(
            'sensor',
            {
                'name': name,
                'type': sensor_type,
            },
            position,
            rotation,
        )


class CameraSensor(Sensor):
    """
    Camera Sensor

    Parent element: Link or Joint
    """
    def __init__(self,
                 name: str,
                 width: int = 320,
                 height: int = 240,
                 horizontal_fov: float = 1.047,
                 clip_near: float = 0.1,
                 clip_far: float = 100.0,
                 position=None,
                 rotation=None):
        """
        Constructor
        :param name: name of the sensor
        :param width: pixel width size of the camera
        :param height: pixel height size of the camera
        :param horizontal_fov: FOV on the horizontal axis (the vertical one is calculated from this and the canvas proportions)
        :param clip_near: Clipping near of the camera frustum
        :param clip_far: Clipping far of the camera frustum
        :param position: Position of the camera
        :param rotation: Rotation (orientation) of the camera
        """
        super().__init__(
            name, 'camera', position, rotation
        )
        camera = xml.etree.ElementTree.SubElement(self, 'camera')
        SDF.sub_element_text(camera, 'horizontal_fov', horizontal_fov)
        image = xml.etree.ElementTree.SubElement(camera, 'image')
        clip = xml.etree.ElementTree.SubElement(camera, 'clip')

        SDF.sub_element_text(image, 'width', width)
        SDF.sub_element_text(image, 'width', height)
        SDF.sub_element_text(clip, 'near', clip_near)
        SDF.sub_element_text(clip, 'far', clip_far)


class TouchSensor(Sensor):
    """
    Touch Sensor element. It references a collision element and transforms it into a touch sensor.

    Parent element: Link or Joint
    """
    def __init__(self, name: str, collision_element):
        """
        Constructor
        :param name: name of the sensor
        :param collision_element: name or reference of the collision element
        :type collision_element: str|SDF.Collision
        """
        super().__init__(
            name,
            'contact',
        )
        collision_element = collision_element if type(collision_element) is str else collision_element.name
        contact = xml.etree.ElementTree.SubElement(self, 'contact')
        SDF.sub_element_text(contact, 'collision', collision_element)
        # SDF.sub_element_text(contact, 'topic', 'topic_{}'.format(collision_element))
