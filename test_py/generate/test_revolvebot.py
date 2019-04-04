from __future__ import absolute_import

import unittest

from pyrevolve.revolve_bot import RevolveBot

class TestRevolveBot(unittest.TestCase):
    """
    Basic tests for RobolveBot body and brain generation
    """

    def test_load_save_yaml(self):
        """
        We load a YAML file and save it
        """

        revolve_bot = RevolveBot()
        revolve_bot.load_file(
            path='experiments/examples/yaml/simple_robot.yaml',
            conf_type='yaml'
        )
        revolve_bot.save_file(
            path='/tmp/revolve_bot.yaml',
            conf_type='yaml'
        )

        revolve_bot2 = RevolveBot()
        revolve_bot2.load_file(
            path='/tmp/revolve_bot.yaml',
            conf_type='yaml'
        )

        self.assertEqual(revolve_bot, revolve_bot2)
