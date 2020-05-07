from __future__ import absolute_import
from __future__ import print_function

import os
import time

from pyrevolve import parser, str_to_address, make_revolve_config
from pyrevolve.angle import Tree, Crossover, Mutator, WorldManager
# from pyrevolve.angle.robogen.spec import make_planar
# from pyrevolve.sdfbuilder import SDF, Model, Pose, Link
from pyrevolve.util import multi_future

from .. import logger
from .. import constants
from .robotmanager import RobotManager
# from ..build import get_builder, to_sdfbot
# from ..scenery import Wall
# from ..spec import get_tree_generator

# Construct a message base from the time. This should make it unique enough
# for consecutive use when the script is restarted.
_a = time.time()
MSG_BASE = int(_a - 14e8 + (_a - int(_a)) * 1e5)


class World(WorldManager):
    """
    A class that is used to manage the world, meaning it provides methods to
    insert / remove robots and request information about where they are.

    The world class contains a number of coroutines, usually from a
    request/response perspective. These methods thus work with two futures -
    one for the request to complete, one for the response to arrive. The
    convention for these methods is to always yield the first future, because it
    has proven problematic to send multiple messages over the same channel,
    so a request is always sent until completion. The methods then return the
    future that resolves when the response is delivered.
    """

    def __init__(self, conf, _private, world_address):
        """
        :param conf:
        """
        world_address = ("127.0.0.1", 11345) if world_address is None else world_address

        conf = make_revolve_config(conf)
        super(World, self).__init__(
            _private=_private,
            world_address=world_address,
            # analyzer_address=str_to_address(conf.analyzer_address),
            output_directory=conf.output_directory,
            builder=None,
            state_update_frequency=conf.pose_update_frequency,
            generator=None,
            restore=conf.restore_directory
        )

        self.conf = conf
        # self.crossover = Crossover(
        #         body_gen=self.generator.body_gen,
        #         brain_gen=self.generator.brain_gen
        # )
        # self.mutator = Mutator(
        #         body_gen=self.generator.body_gen,
        #         brain_gen=self.generator.brain_gen,
        #         p_duplicate_subtree=conf.p_duplicate_subtree,
        #         p_swap_subtree=conf.p_swap_subtree,
        #         p_delete_subtree=conf.p_delete_subtree,
        #         p_remove_brain_connection=conf.p_remove_brain_connection,
        #         p_delete_hidden_neuron=conf.p_delete_hidden_neuron
        # )

        # Set to true whenever a reproduction sequence is going on
        # to prevent another one from starting (which cannot happen now
        # but might in a more complicated yielding structure).
        self._reproducing = False

        # Write settings to config file
        if None:#self.output_directory:
            parser.record(
                args=conf,
                file=os.path.join(self.output_directory, "settings.conf")
            )

    @classmethod
    async def create(cls, conf, world_address=None):
        """
        Coroutine to instantiate a Revolve.Angle WorldManager
        :param conf:
        :param world_address:
        :return:
        """
        self = cls(_private=cls._PRIVATE, conf=conf, world_address=world_address)
        await self._init()
        return self

    def robots_header(self):
        """
        Extends the robots header with a max age
        :return:
        """
        return RobotManager.header()

    def create_robot_manager(
            self,
            robot,
            position,
            time,
    ):
        """
        Overriding with robot manager with more capabilities.
        :param robot:
        :param position:
        :param time:
        :return:
        """
        return RobotManager(
            conf=self.conf,
            robot=robot,
            position=position,
            time=time,
            battery_level=robot.battery_level,
        )

    async def add_highlight(self, position, color):
        """
        Adds a circular highlight at the given position.
        :param position:
        :param color:
        :return:
        """
        hl = Highlight("highlight_" + str(self.get_robot_id()), color)
        position = position.copy()
        position.z = 0
        hl.set_position(position)
        sdf = SDF(elements=[hl])
        future = await (self.insert_model(sdf))
        return future, hl

    async def generate_population(self, n):
        """
        Generates population of `n` valid robots robots.

        :param n: Number of robots
        :return: Future with a list of valid robot trees and corresponding
                 bounding boxes.
        """
        logger.info("Generating population of size %d..." % n)
        trees = []
        bboxes = []

        for _ in range(n):
            gen = await (self.generate_valid_robot())
            if not gen:
                return None

            tree, _, bbox = gen
            trees.append(tree)
            bboxes.append(bbox)

        return trees, bboxes

    async def insert_population(self, trees, poses):
        """
        :param trees:
        :type trees: list[Tree]
        :param poses: Iterable of (x, y, z) positions to insert.
        :type poses: list[Pose]
        :return:
        """
        futures = []
        for tree, pose in zip(trees, poses):
            future = self.insert_robot(tree, pose)
            futures.append(future)

        future = multi_future(futures)
        future.add_done_callback(
            lambda _: logger.info("Done inserting population."))

        # Awaiting this immediately will lock the program
        update_state_future = self.set_state_update_frequency(
            freq=self.state_update_frequency
        )
        await update_state_future

        return future

    def to_sdfbot(self, robot, robot_name, initial_battery=0.0):
        """
        :param robot:
        :param robot_name:
        :param initial_battery:
        :return:
        """
        return to_sdfbot(
            robot=robot,
            name=robot_name,
            builder=None,
            conf=self.conf,
            battery_charge=initial_battery
        )

    async def build_walls(self, points):
        """
        Builds a wall defined by the given points, used to shield the
        arena.
        :param points:
        :return: Future that resolves when all walls have been inserted.
        """
        futures = []
        length = len(points)
        for i in range(length):
            start = points[i]
            end = points[(i + 1) % length]
            wall = Wall(
                name="wall_%d" % i,
                start=start,
                end=end,
                thickness=constants.WALL_THICKNESS,
                height=constants.WALL_HEIGHT)
            future = self.insert_model(SDF(elements=[wall]))
            futures.append(future)

        return multi_future(futures)

    async def attempt_mate(self, ra, rb):
        """
        Attempts mating between two robots.
        :param ra:
        :param rb:
        :return:
        """
        logger.info("Attempting mating between `{}` and `{}`...".format(
            ra.name,
            rb.name))

        # Attempt to create a child through crossover
        success, child = self.crossover.crossover(ra.tree, rb.tree)
        if not success:
            logger.info("Crossover failed.")
            return False

        # Apply mutation
        logger.info("Crossover succeeded, applying mutation...")
        self.mutator.mutate(child, in_place=True)

        # if self.conf.enforce_planarity:
            # make_planar(child.root)

        _, outputs, _ = child.root.io_count(recursive=True)
        if not outputs:
            logger.info("Evolution resulted in child without motors.")
            return False

        # Check if the robot body is valid
        ret = await (self.analyze_tree(child))
        if ret is None or ret[0]:
            logger.info("Intersecting body parts: Miscarriage.")
            return False

        logger.info("Viable child created.")
        return child, ret[1]


# class Highlight(Model):
#     """
#     Model to highlight newly inserted robots / selected parents
#     """
#
#     def __init__(self, name, color, **kwargs):
#         super(Highlight, self).__init__(name, static=True, **kwargs)
#         self.highlight = Link("hl_link")
#         self.highlight.make_cylinder(10e10, 0.4, 0.001, collision=False)
#         r, g, b, a = color
#         self.highlight.make_color(r, g, b, a)
#         self.add_element(self.highlight)
