#!/usr/bin/env python3

# Global / system
import os
import uuid

# Revolve
from ..connection import VrepConnection
from ...logging import logger
from ...tol.build import get_simulation_robot

from pyrevolve.build.sdf.builder import RobotBuilder, BodyBuilder, NeuralNetBuilder
from pyrevolve.spec import default_neural_net
from pyrevolve.tol.spec import get_body_spec, get_brain_spec


class WorldManager(object):
    """
    Class for basic world management such as inserting / deleting
    models
    """
    # Object used to make constructor private
    _PRIVATE = object()

    def __init__(
            self,
            conf,
            _private=None,
            world_address=None,
            world_port=None,
    ):
        """

        :param _private:
        :return:
        """
        if _private is not self._PRIVATE:
            raise ValueError("The manager cannot be directly constructed,"
                             "rather the `create` coroutine should be used.")

        self.conf = conf
        self.world_address = world_address
        self.world_port = world_port

        self.conf.enable_wheel_parts = False

        self._vrep_connection = None

        # TODO generic stuff
        self._robot_counter = 0
        self.builder = RobotBuilder(
            body_builder=BodyBuilder(get_body_spec(self.conf), self.conf),
            brain_builder=NeuralNetBuilder(get_brain_spec(self.conf))
        )

    @classmethod
    def create(
            cls,
            conf,
            world_address="127.0.0.1",
            world_port=19997,
    ):
        """
        :param conf:
        :param world_address:
        :param world_port:
        :return:
        """
        self = cls(
            _private=cls._PRIVATE,
            conf=conf,
            world_address=world_address,
            world_port=world_port,
        )
        self._init()
        return self

    def _init(self):
        """
        Initializes connections for the world manager
        :return:
        """
        if self._vrep_connection is not None:
            self._vrep_connection.close()

        # Initialize the manager connections as well as the general request
        # handler
        self._vrep_connection = VrepConnection(address=self.world_address, port=self.world_port)
        # self._vrep_connection = VrepConnection()
        self._vrep_connection.connect()

        self._vrep_connection.reset_world()
        self._vrep_connection.load_scene(
            os.path.abspath(os.path.join("worlds", "vrep_base_world.ttt"))
        )

    def pause(self, pause=True):
        """
        Pause / unpause the world
        :param pause:
        """
        if pause:
            logger.debug("Pausing the world.")
        else:
            logger.debug("Resuming the world.")

        self._vrep_connection.pause(pause)

    def reset(self):
        """
        Reset the world.
        """
        logger.debug("Resetting the world state.")
        self._vrep_connection.reset_world()

    def insert_model(self, sdf):
        """
        Insert a model wrapped in an SDF tag into the world. Make
        sure it has a unique name, as it will be literally inserted into the
        world.

        :param sdf:
        :type sdf: SDF

        TODO this works only if the simulator is on the same host of the manager, fixit

        :return:
        """

        # function parameters
        filename = "{}.sdf".format(str(uuid.uuid4()))
        ignore_missing_values = True  # default False
        hide_collision_links = True
        hide_joints = True
        convex_decompose = True
        show_convex_decomposition_dlg = False
        create_visual_if_none = True
        center_model = True
        prepare_model = True
        no_self_collision = True
        position_ctrl = True

        # Create SDF file in tmp/
        filename = os.path.abspath(os.path.join("tmp", filename))
        file = open(filename, "w")
        file.write(str(sdf))

        self._vrep_connection.call_script_function("importSDF",
                                                   input_strings=[filename],
                                                   # input_ints=[ignore_missing_values,
                                                   #             hide_collision_links,
                                                   #             hide_joints,
                                                   #             convex_decompose,
                                                   #             show_convex_decomposition_dlg,
                                                   #             create_visual_if_none,
                                                   #             center_model,
                                                   #             prepare_model,
                                                   #             no_self_collision,
                                                   #             position_ctrl]
                                                   )

        # os.remove(filename)
        # TODO return robot handle

    def insert_robot(
            self,
            tree,
            pose,
            robot_name=None,
            initial_battery=0.0,
            parents=None
    ):
        """
        Inserts a robot into the world. This consists of two steps:

        - Sending the insert request message
        - Receiving a ModelInfo response

        This method is a coroutine because of the first step, writing
        the message must be yielded since PyGazebo doesn't appear to
        support writing multiple messages simultaneously. For the response,
        i.e. the message that confirms the robot has been inserted, a
        future is returned.

        :param tree:
        :type tree: Tree
        :param pose: Insertion pose
        :type pose: Pose
        :param robot_name: Robot name
        :type robot_name: str
        :param initial_battery: Initial battery level
        :param parents:
        :return: A future that resolves with the created `Robot` object.
        """
        self._robot_counter += 1
        robot_id = self._robot_counter
        if robot_name is None:
            robot_name = "gen__{}".format(robot_id)

        try:
            os.mkdir("tmp")
        except FileExistsError:
            pass

        robot = tree.to_robot(robot_id)
        sdf = self.get_simulation_sdf(
            robot=robot,
            robot_name=robot_name,
            initial_battery=initial_battery)
        sdf.elements[0].set_pose(pose)

        # if self.output_directory:
        #     robot_file_path = os.path.join(
        #         self.output_directory,
        #         'robot_{}.sdf'.format(robot_id)
        #     )
        #     with open(robot_file_path, 'w') as f:
        #         f.write(str(sdf))

        self.insert_model(sdf)

    def delete_model(self, name):
        """
        Deletes the model with the given name from the world.
        :param name:
        :param req: Type of request to use. If you are going to
        delete a robot, I suggest using `delete_robot` rather than `entity_delete`
        because this attempts to prevent some issues with segmentation faults
        occurring from deleting sensors.
        :return:
        """
        self._vrep_connection.remove_model(name)

    # TODO stuff generic for gazebo e vrep

    def get_simulation_sdf(self, robot, robot_name, initial_battery=0.0):
        """
        :param robot:
        :param robot_name:
        :param initial_battery:
        :return:
        """

        return get_simulation_robot(
            robot=robot,
            name=robot_name,
            builder=self.builder,
            conf=self.conf,
            battery_charge=initial_battery
        )
