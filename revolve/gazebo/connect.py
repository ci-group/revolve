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
    # Object used to make constructor private
    _PRIVATE = object()

    def __init__(self, manager, request_class, request_type,
                 response_class, response_type,
                 advertise, subscribe, id_attr, msg_id_base,
                 _private=None):
        """
        Private constructor, use the `create` coroutine instead.
        :param manager:
        :return:
        """
        if _private is not self._PRIVATE:
            raise ValueError("The RequestHandler cannot be directly constructed,"
                             "rather the `create` coroutine should be used.")

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

    @classmethod
    @trollius.coroutine
    def create(cls, manager,
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
        :param request_class:
        :param request_type:
        :param response_class:
        :param response_type:
        :param advertise:
        :param subscribe:
        :param id_attr:
        :param msg_id_base:
        :return:
        """
        handler = cls(manager, request_class, request_type, response_class, response_type,
                      advertise, subscribe, id_attr, msg_id_base, cls._PRIVATE)
        yield From(handler._init())
        raise Return(handler)

    @trollius.coroutine
    def _init(self):
        """
        :return:
        """
        if self.publisher is not None:
            return

        self.subscriber = self.manager.subscribe(self.subscribe,
                               self.response_type,
                               self._callback)
        self.publisher = yield From(self.manager.advertise(
            self.advertise, self.request_type))

        yield From(self.subscriber.wait_for_connection())
        yield From(self.publisher.wait_for_listener())

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
        msg_id = str(msg_id)
        del self.responses[msg_id]
        del self.callbacks[msg_id]

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

        return self.do_request(req, callback)

    def do_request(self, msg, callback=None):
        """
        Performs a request. The only requirement
        of `msg` is that it has an `id` attribute.

        Returns a future, you should yield this to make
        sure the request is completed.

        :param msg: Message object to publish
        :param callback:
        :return:
        """
        msg_id = str(self.get_id_from_msg(msg))
        if msg_id in self.responses:
            raise RuntimeError("Duplicate request ID: %s" % msg_id)

        self.responses[msg_id] = None
        self.callbacks[msg_id] = callback
        return self.publisher.publish(msg)
