from .posable import Posable
from .joint import Joint


class Model(Posable):
    """
    SDF "model" type
    """
    TAG_NAME = 'model'

    def __init__(self, name, static=False, **kwargs):
        """

        :param name:
        :param kwargs:
        :return:
        """
        super(Model, self).__init__(name, **kwargs)
        self.static = static

    def get_joints(self):
        """
        Returns all child elements in this model which are joints.
        :return:
        """
        return self.get_elements_of_type(Joint)

    def render_elements(self):
        """
        Returns all elements plus the "static" property.
        :return:
        """
        #TODO change static to true/false (minor case)
        static = "<static>%d</static>" % int(self.static)
        return super(Model, self).render_elements() + [static]
