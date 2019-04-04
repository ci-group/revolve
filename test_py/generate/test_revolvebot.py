import unittest

from pyrevolve.revolve_bot import RevolveBot


class TestRevolveBot(unittest.TestCase):
    """
    Basic tests for RobolveBot body and brain generation
    """
    def revolve_bot_equal(self, roba, robb):
        self._revolve_bot_body_equal(roba._body, robb._body)
        self._revolve_bot_brain_equal(roba._brain, robb._brain)

    def _revolve_bot_body_equal(self, bodya, bodyb):
        self.assertEqual(type(bodya), type(bodyb))

    def _revolve_bot_brain_equal(self, braina, brainb):
        self.assertEqual(type(braina), type(brainb))

    def _proto_test(self, filename):

        revolve_bot = RevolveBot()
        revolve_bot.load_file(
            path=filename,
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

        self.revolve_bot_equal(revolve_bot, revolve_bot2)

    def test_load_save_yaml(self):
        """
        We load a YAML file and save it
        """
        self._proto_test('experiments/examples/yaml/simple_robot.yaml')
        self._proto_test('experiments/examples/yaml/spider.yaml')
        self._proto_test('experiments/examples/yaml/gecko.yaml')
        self._proto_test('experiments/examples/yaml/snake.yaml')
