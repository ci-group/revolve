import xml.etree.ElementTree
from pyrevolve import URDF


class Sensor(URDF.Posable):
    SENSOR_TYPE = None

    """
    Generic SDF sensor.

    Parent element: Link or Joint
    """
    def __init__(self, name: str, link, module, position=None, rotation=None):
        super().__init__(
            'sensor',
            {
                'name': name,
                'type': self.SENSOR_TYPE,
            },
            position,
            rotation,
        )
        self._name = name
        self._link = link
        self._module = module

    def to_robot_config_sdf(self):
        return xml.etree.ElementTree.Element('rv:sensor', {
            'link': self._link.name,
            'sensor': self._name,
            'type': self.SENSOR_TYPE,
            'id': '{}_sensor'.format(self._link.name),
            'part_id': self._module.id,
        })


class IMUSensor(Sensor):
    SENSOR_TYPE = 'imu'
    """
    IMU Sensor

    Parent element: Link or Joint
    """
    def __init__(self, name: str, link, module):
        super().__init__(name, link, module)
        URDF.sub_element_text(self, 'always_on', True)


class CameraSensor(Sensor):
    SENSOR_TYPE = 'camera'
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
        URDF.sub_element_text(camera, 'horizontal_fov', horizontal_fov)
        image = xml.etree.ElementTree.SubElement(camera, 'image')
        clip = xml.etree.ElementTree.SubElement(camera, 'clip')

        URDF.sub_element_text(image, 'width', width)
        URDF.sub_element_text(image, 'width', height)
        URDF.sub_element_text(clip, 'near', clip_near)
        URDF.sub_element_text(clip, 'far', clip_far)

        URDF.sub_element_text(self, 'always_on', True)


class TouchSensor(Sensor):
    SENSOR_TYPE = 'contact'
    """
    Touch Sensor element. It references a collision element and transforms it into a touch sensor.

    Parent element: Link or Joint
    """
    def __init__(self, name: str, collision_element, link, module):
        """
        Constructor
        :param name: name of the sensor
        :param collision_element: name or reference of the collision element
        :type collision_element: str|SDF.Collision
        """
        super().__init__(name, link, module)
        collision_element = collision_element if type(collision_element) is str else collision_element.name
        contact = xml.etree.ElementTree.SubElement(self, 'contact')
        URDF.sub_element_text(contact, 'collision', collision_element)
        # SDF.sub_element_text(contact, 'topic', 'topic_{}'.format(collision_element))
        # SDF.sub_element_text(self, 'update_rate', 8.0)
        URDF.sub_element_text(self, 'always_on', True)
