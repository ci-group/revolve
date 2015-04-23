"""
Demonstrates creating a simple SDF bot from a spec and a YAML file.
"""
import sys
import os
from sdfbuilder.base import SDF


# Add module to path
cur_path = os.path.dirname(os.path.realpath(__file__))
module_path = os.path.join(cur_path, '..', '..')
sys.path.append(module_path)

# Module imports
from revolve.spec import SpecImplementation, PartSpec
from revolve.builder.sdf.body import Box
from revolve.convert.yaml import yaml_to_protobuf
from revolve.builder.sdf import Builder as SdfBuilder


# Define two simple box body parts
class Block(Box):
    X = 0.10
    Y = 0.20
    Z = 0.30
    MASS = 0.5


class CoreComponent(Box):
    X = 0.5
    Y = 0.5
    Z = 0.5
    MASS = 10.0


# Define a spec with a simple block, with two aliases
spec = SpecImplementation(
    parts={
        ("CoreComponent", "E"): PartSpec(
            body_part=CoreComponent,
            arity=6,
            input_neurons=4
        ),
        ("Block", "B"): PartSpec(
            body_part=Block,
            arity=6,
            output_neurons=1
        ),
    }
)

# Create bot YAML
bot = '''\
---
body:
  id: Core
  type: E
  children:
    0:
      id: Sub1
      type: B
      orientation: 45
    1:
      id: Sub2
      type: Block
'''

# Convert the YAML file to protobuf
proto = yaml_to_protobuf(spec, bot)

# Convert the protobuf to SDF
builder = SdfBuilder(spec, None)
model = builder.get_sdf_model(proto, "test_bot", validate=True)

# Create SDF and output
sdf = SDF()
sdf.add_element(model)
print(str(sdf))