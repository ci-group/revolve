from sdfbuilder import Element
from sdfbuilder.util import number_format as nf
from ....spec import Neuron as ProtoNeuron, NeuralConnection as ProtoNeuralConnection


class Neuron(Element):
    """
    Plugin neuron element.
    """
    TAG_NAME = 'rv:neuron'

    def __init__(self, neuron, params):
        """
        :param neuron: Protobuf neuron
        :type neuron: ProtoNeuron
        :param params:
        :return:
        """
        super(Neuron, self).__init__()
        self.neuron = neuron
        self.params = params

    def render_attributes(self):
        """
        Adds type / ID / layer attributes
        """
        attrs = super(Neuron, self).render_attributes()
        attrs.update({
            'layer': self.neuron.layer,
            'type': self.neuron.type,
            'id': self.neuron.id
        })

        if self.neuron.HasField("partId"):
            attrs['part_id'] = self.neuron.partId

        return attrs

    def render_elements(self):
        """
        Adds attributes as elements
        """
        elms = [Element(tag_name='rv:'+param, body=nf(self.params[param])) for param in self.params]
        return super(Neuron, self).render_elements() + elms


class NeuralConnection(Element):
    """
    Plugin neural connection element.
    """
    TAG_NAME = 'rv:neural_connection'

    def __init__(self, conn):
        """
        :param conn:
        :type conn: ProtoNeuralConnection
        :return:
        """
        super(NeuralConnection, self).__init__()
        self.conn = conn

    def render_attributes(self):
        """
        """
        attrs = super(NeuralConnection, self).render_attributes()
        attrs.update({
            'src': self.conn.src,
            'dst': self.conn.dst,
            'weight': nf(self.conn.weight)
        })

        return attrs