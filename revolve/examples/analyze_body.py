"""
Generates a bot using the code in `generated_sdf`,
and sends it to the body analyzer to have it analyzed.

Requires an instance of the body analyzer to be running.
"""
from .generated_sdf import generate_sdf_robot
from ..analyze.sdf import analyze_body

sdf = generate_sdf_robot()
intersections, bbox = analyze_body(sdf)

if bbox:
    print("Model bounding box: (%f, %f, %f)" % bbox)

if intersections:
    print("Invalid model - intersections detected.")
else:
    print("No model intersections detected!")
