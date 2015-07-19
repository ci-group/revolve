import trollius
from trollius import From, Return
import pygazebo
from pygazebo.msg import request_pb2, response_pb2

# Default connection address to keep things DRY. This is an array
# rather than a tuple, so it is writeable as long as you change
# the separate elements.
default_address = ["127.0.0.1", 11345]


@trollius.coroutine
def connect(address=default_address):
    manager = yield From(pygazebo.connect(address=tuple(address)))
    raise Return(manager)


class RequestHandler(object):
    """
    Utility class to send `Request` messages and accept
    responses to them.
    """

    def __init__(self, manager,
                 request_class=request_pb2.Request,
                 request_type='gazebo.msgs.Request',
                 response_class=response_pb2.Response,
                 response_type='gazebo.msgs.Response',
                 advertise='/gazebo/default/request',
                 subscribe='/gazebo/default/response',
                 id_attr='id',
                 msg_id_base=0):
        """
        :param manager:
        :return:
        """
        self.id_attr = id_attr
        self.response_type = response_type
        self.request_type = request_type
        self.request_class = request_class
        self.subscribe = subscribe
        self.advertise = advertise
        self.response_class = response_class
        self.manager = manager
        self.responses = {}
        self.callbacks = {}
        self.publisher = None
        self.msg_id = msg_id_base

    def _initialize(self):
        """
        :return:
        """
        if self.publisher is not None:
            raise Return(None)

        self.manager.subscribe(self.subscribe,
                               self.response_type,
                               self._callback)
        self.publisher = yield From(self.manager.advertise(
            self.advertise, self.request_type))

    def _callback(self, data):
        """
        :param data:
        :return:
        """
        msg = self.response_class()
        msg.ParseFromString(data)

        msg_id = str(self.get_id_from_msg(msg))
        if msg_id not in self.responses:
            # Message was not requested here, ignore it
            return

        self.responses[msg_id] = msg

        # If a callback is registered, use it
        if self.callbacks[msg_id] is not None:
            self.callbacks[msg_id](msg)

    def get_id_from_msg(self, msg):
        """
        Returns the ID given a protobuf message.
        :param msg:
        :return:
        """
        return getattr(msg, self.id_attr)

    def get_msg_id(self):
        """
        Message ID sequencer.
        :return:
        """
        self.msg_id += 1
        return self.msg_id

    def get_response(self, msg_id):
        """
        :param msg_id:
        :return:
        """
        return self.responses.get(msg_id, None)

    def handled(self, msg_id):
        """
        Deletes a message from the current response history.
        :param msg_id:
        :return:
        """
        del self.responses[msg_id]
        del self.callbacks[msg_id]

    @trollius.coroutine
    def do_gazebo_request(self, msg_id, data=None, dbl_data=None, callback=None):
        """
        Convenience wrapper to use `do_request` with a default Gazebo
        `Request` message.
        :param msg_id:
        :type msg_id: int
        :param data:
        :param dbl_data:
        :param callback:
        :return:
        """
        req = request_pb2.Request()
        req.id = msg_id

        if data is not None:
            req.data = data

        if dbl_data is not None:
            req.dbl_data = dbl_data

        yield From(self.do_request(req, callback))

    @trollius.coroutine
    def do_request(self, msg, callback=None):
        """
        Coroutine to perform a request. The only requirement
        of `msg` is that it has an `id` attribute.

        :param msg: Message object to publish
        :param callback:
        :return:
        """
        msg_id = str(self.get_id_from_msg(msg))
        if msg_id in self.responses:
            raise RuntimeError("Duplicate request ID: %s" % msg_id)

        yield From(self._initialize())
        self.responses[msg_id] = None
        self.callbacks[msg_id] = callback
        yield From(self.publisher.publish(msg))
