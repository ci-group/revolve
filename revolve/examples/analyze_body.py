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
