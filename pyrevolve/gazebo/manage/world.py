#!/usr/bin/env python3
from __future__ import absolute_import, annotations

import time
from pygazebo import Publisher, Manager as PyGazeboManager
from pygazebo.msg import world_control_pb2

from pyrevolve.gazebo.connect import connect, RequestHandler
from pyrevolve.custom_logging.logger import logger

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Optional, Any


# Construct a message base from the time. This should make
# it unique enough for consecutive use when the script
# is restarted.
_a = time.time()
MSG_BASE = int(_a - 14e8 + (_a - int(_a)) * 1e5)


class WorldManager(object):
    """
    Class for basic world management such as inserting / deleting
    models
    """
    # Object used to make constructor private
    _PRIVATE = object()

    def __init__(
            self,
            _private=None,
            world_address: (str, int) = None,
    ):
        """
        This constructor is private because a constructor cannot be async. Use create instead.
        :param _private: to make the constructor private
        :param world_address: simulator address
        """
        if _private is not self._PRIVATE:
            raise ValueError("The manager cannot be directly constructed,"
                             "rather the `create` coroutine should be used.")

        self.world_address: (str, int) = world_address

        # These are later initialized in `self._init()`
        # Calling the create function instead of the constructor directly ensures
        #  that these values are correctly initialized
        self.manager: PyGazeboManager = None
        self.world_control: Publisher = None
        self.request_handler: RequestHandler = None

    @classmethod
    async def create(
            cls,
            world_address: (str, int) = ("127.0.0.1", 11345),
    ) -> WorldManager:
        """
        Substitute async constructor. It creates and initializes the connection to the simulator.
        :param world_address: address to connect to
        :return: The WorldManager object initialized and connected
        """
        self = cls(
            _private=cls._PRIVATE,
            world_address=world_address,
        )
        await self._init()
        return self

    async def disconnect(self):
        await self.manager.stop()
        await self.request_handler.stop()

    async def _init(self) -> None:
        """
        Initializes connections for the world manager
        """
        if self.manager is not None:
            return

        # Initialize the manager connections as well as the general request
        # handler
        self.manager: PyGazeboManager = await connect(self.world_address[0], self.world_address[1])

        self.world_control: Publisher = await self.manager.advertise(
            topic_name='/gazebo/default/world_control',
            msg_type='gazebo.msgs.WorldControl'
        )

        self.request_handler: RequestHandler = await RequestHandler.create(
            manager=self.manager,
            msg_id_base=MSG_BASE
        )

        # Wait for connections
        await self.world_control.wait_for_listener()

    async def pause(self, pause: bool = True) -> None:
        """
        Pause / unpause the world
        :param pause:
        :return: Future for the published message
        """
        if pause:
            logger.info("Pausing the world.")
        else:
            logger.info("Resuming the world.")

        msg = world_control_pb2.WorldControl()
        msg.pause = pause
        await self.world_control.publish(msg)

    async def reset(
            self,
            rall: bool = False,
            time_only: bool = True,
            model_only: bool = False
    ) -> None:
        """
        Reset the world. Defaults to time only, since that appears to be the
        only thing that is working by default anyway.
        :param rall: reset all
        :param model_only: resets only the models
        :param time_only: resets only the time
        """
        logger.info("Resetting the world state.")
        msg = world_control_pb2.WorldControl()
        msg.reset.all = rall
        msg.reset.model_only = model_only
        msg.reset.time_only = time_only
        await self.world_control.publish(msg)

    async def insert_model(self, sdf, timeout: Optional[float] = None) -> Any:
        """
        Insert a model wrapped in an SDF tag into the world. Make
        sure it has a unique name, as it will be literally inserted into the
        world.

        This coroutine yields until the request has been successfully sent.
        It returns a future that resolves when a response has been received.
        The optional given callback is added to this future.

        :param sdf:
        :type sdf: SDF
        :param timeout: Life span of the model
        :type timeout: float|None
        :return: the message response
        """
        return await self.request_handler.do_gazebo_request(
            request="insert_sdf",
            data=str(sdf),
            dbl_data=timeout,
        )

    async def delete_model(
            self,
            name: str,
            req: str = "entity_delete"
    ) -> Any:
        """
        Deletes the model with the given name from the world.
        :param name:
        :param req: Type of request to use. If you are going to
        delete a robot, I suggest using `delete_robot` rather than `entity_delete`
        because this attempts to prevent some issues with segmentation faults
        occurring from deleting sensors.
        :return: the message response
        """
        return await self.request_handler.do_gazebo_request(
            request=req,
            data=name
        )
