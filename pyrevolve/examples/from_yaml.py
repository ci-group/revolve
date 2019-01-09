from __future__ import absolute_import
from __future__ import print_function

from pyrevolve.build.sdf import RobotBuilder
from pyrevolve.build.sdf import BodyBuilder
from pyrevolve.build.sdf import NeuralNetBuilder
from pyrevolve.convert import yaml_to_robot
from pyrevolve.sdfbuilder import SDF
from pyrevolve.sdfbuilder.math import Vector3

from .generated_sdf import body_spec, brain_spec

bot_yaml = '''
---
body:
  id          : Core
  type        : Core
  children:
    1:
      id: Hinge
      type: Hinge
      params:
        length: 0.5
        red: 1.0
        green: 0.0
        blue: 0.0
    4:
      id: Wheel
      type: Wheel
      params:
        red: 0.0
        green: 1.0
        blue: 0.0
    5:
      id: Wheel2
      type: Wheel
      params:
        red: 0.0
        green: 1.0
        blue: 0.0
brain:
  params:
    Wheel-out-0:
      type: Oscillator
      period: 3
    Wheel2-out-0:
      type: Oscillator
      period: 3
'''

bot = yaml_to_robot(body_spec, brain_spec, bot_yaml)
builder = RobotBuilder(BodyBuilder(body_spec), NeuralNetBuilder(brain_spec))
model = builder.get_sdf_model(bot, "libRobotControlPlugin.so")
model.translate(Vector3(0, 0, 0.5))
sdf = SDF()
sdf.add_element(model)
print(str(sdf))
