from __future__ import print_function
import sys
from sdfbuilder import Link, Model, SDF
from sdfbuilder.math import Vector3

# Create two similar boxes
link1 = Link("box1")
link1.make_box(1.0, 0.1, 0.3, 0.5)

link2 = Link("box2")
link2.make_box(1.0, 0.1, 0.3, 0.5)

# Align the top of box2 with the front of box1
link2.align(
    Vector3(0, 0, 0.25),
    Vector3(0, 0, -1),
    Vector3(1, 0, 0),

    Vector3(0, -0.15, 0),
    Vector3(0, 1, 0),
    Vector3(0, 0, 1),

    link1
)

if __name__ == '__main__':
    sdf = SDF()
    model = Model("my_model")
    model.add_element(link1)
    model.add_element(link2)
    sdf.add_element(model)
    print(str(sdf))
