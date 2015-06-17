from sdfbuilder import SDF
from sdfbuilder.math import Vector3
from .generated_sdf import body_spec, brain_spec
from revolve.build.sdf import RobotBuilder, BodyBuilder, NeuralNetBuilder
from revolve.convert import yaml_to_robot

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
'''

bot = yaml_to_robot(body_spec, brain_spec, bot_yaml)
builder = RobotBuilder(BodyBuilder(body_spec), NeuralNetBuilder(brain_spec))
model = builder.get_sdf_model(bot, None)
model.translate(Vector3(0, 0, 0.5))
sdf = SDF()
sdf.add_element(model)
print(str(sdf))
