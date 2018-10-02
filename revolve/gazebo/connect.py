import trollius
from trollius import From, Return, Future
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

    def __init__(
            self,
            manager,
            request_class,
            request_type,
            response_class,
            response_type,
            advertise,
            subscribe,
            id_attr,
            request_attr,
            msg_id_base,
            wait_for_subscriber,
            wait_for_publisher,
            _private=None
    ):
        """
        Private constructor, use the `create` coroutine instead.
        :param manager:
        :return:
        """
        if _private is not self._PRIVATE:
            raise ValueError("RequestHandler cannot be directly constructed,"
                             "rather the `create` coroutine should be used.")

        self.id_attr = id_attr
        self.request_attr = request_attr
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
        self.wait_for_publisher = wait_for_publisher
        self.wait_for_subscriber = wait_for_subscriber
        self.msg_id = int(msg_id_base)

    @classmethod
    @trollius.coroutine
    def create(
            cls,
            manager,
            request_class=request_pb2.Request,
            request_type='gazebo.msgs.Request',
            response_class=response_pb2.Response,
            response_type='gazebo.msgs.Response',
            advertise='/gazebo/default/request',
            subscribe='/gazebo/default/response',
            id_attr='id',
            request_attr='request',
            wait_for_subscriber=True,
            wait_for_publisher=True,
            msg_id_base=0
    ):
        """

        :param wait_for_publisher:
        :param wait_for_subscriber:
        :param manager:
        :param request_class:
        :param request_type:
        :param response_class:
        :param response_type:
        :param advertise:
        :param subscribe:
        :param id_attr:
        :param request_attr:
        :param msg_id_base:
        :return:
        """
        handler = cls(
                manager,
                request_class,
                request_type,
                response_class,
                response_type,
                advertise,
                subscribe,
                id_attr,
                request_attr,
                msg_id_base,
                wait_for_subscriber,
                wait_for_publisher,
                cls._PRIVATE
        )
        yield From(handler._init())
        raise Return(handler)

    @trollius.coroutine
    def _init(self):
        """
        :return:
        """
        if self.publisher is not None:
            return

        self.subscriber = self.manager.subscribe(
            self.subscribe,
            self.response_type,
            self._callback
        )
        self.publisher = yield From(self.manager.advertise(
            self.advertise, self.request_type))

        if self.wait_for_publisher:
            yield From(self.subscriber.wait_for_connection())

        if self.wait_for_subscriber:
            yield From(self.publisher.wait_for_listener())

    def _callback(self, data):
        """
        :param data:
        :return:
        """
        msg = self.response_class()
        msg.ParseFromString(data)

        msg_id = str(self.get_id_from_msg(msg))
        request_type = str(self.get_request_type_from_msg(msg))
        req, cb = self._get_response_map(request_type)

        if msg_id not in req:
            # Message was not requested here, ignore it
            return

        req[msg_id] = msg

        # Call the future's set_result
        cb[msg_id].set_result(msg)
        self._handled(request_type, msg_id)

    def get_id_from_msg(self, msg):
        """
        Returns the ID given a protobuf message.
        :param msg:
        :return:
        """
        return getattr(msg, self.id_attr)

    def get_request_type_from_msg(self, msg):
        """
        Returns the request type from a protobuf message.
        :param msg:
        :return:
        """
        return getattr(msg, self.request_attr)

    def get_msg_id(self):
        """
        Message ID sequencer.
        :return:
        """
        self.msg_id += 1
        return self.msg_id

    def _handled(self, msg_type, msg_id):
        """
        Deletes a message from the current response history.
        :param msg_type:
        :param msg_id:
        :return:
        """
        msg_id = str(msg_id)
        msg_type = str(msg_type)
        req, cb = self._get_response_map(msg_type)

        del req[msg_id]
        del cb[msg_id]

    @trollius.coroutine
    def do_gazebo_request(
            self,
            request,
            data=None,
            dbl_data=None,
            msg_id=None
    ):
        """
        Convenience wrapper to use `do_request` with a default Gazebo
        `Request` message. See that method for more info.

        :param request:
        :type request: str
        :param data:
        :param dbl_data:
        :param msg_id: Force the message to use this ID. Sequencer is used if no
                       message ID is specified.
        :type msg_id: int
        :return:
        """
        if msg_id is None:
            msg_id = self.get_msg_id()

        req = request_pb2.Request()
        req.id = msg_id
        req.request = request

        if data is not None:
            req.data = data

        if dbl_data is not None:
            req.dbl_data = dbl_data

        future = yield From(self.do_request(req))
        raise Return(future)

    def _get_response_map(self, request_type):
        """

        :param request_type:
        :return:
        :rtype: dict
        """
        if request_type not in self.responses:
            self.responses[request_type] = {}
            self.callbacks[request_type] = {}

        return self.responses[request_type], self.callbacks[request_type]

    @trollius.coroutine
    def do_request(self, msg):
        """
        Performs a request. The only requirement
        of `msg` is that it has an `id` attribute.

        Publishing of the request is always yielded to prevent multiple messages
        from going over the same pipe. The returned future is for the response.

        :param msg: Message object to publish
        :return:
        """
        msg_id = str(self.get_id_from_msg(msg))
        request_type = str(self.get_request_type_from_msg(msg))
        req, cb = self._get_response_map(request_type)

        if msg_id in req:
            raise RuntimeError(
                    "Duplicate request ID: `{}` for type `{}`".format(
                            msg_id, request_type))

        future = Future()
        req[msg_id] = None
        cb[msg_id] = future
        yield From(self.publisher.publish(msg))
        raise Return(future)
