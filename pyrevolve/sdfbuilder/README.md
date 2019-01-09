# SDF Builder
Pragmatic utility library for building SDF files, written in Python.

# Why?
Because writing SDF files manually causes a headache, changing little things often requires changes
everywhere. SDF Builder simplifies this by allowing you to align elements with each other rather than
positioning them absolutely.

# Features
- Wrappers over the most common SDF elements (well.. see examples)
- Simple vector math library based on good old `transformations.py`
- Item alignment, specify how two elements (links, collisions, etc) align with each other rather than setting their exact positions.
- Compound inertia tensors, just add positioned `Collision` elements to
  your `Link`s, `Link.calculate_inertial()` will set the correct inertia
  tensor for you.

# Examples
You can find some examples uses in the `sdfbuilder/examples` directory. The best
place to start is probably `features.py` which shows off a bunch of features at
the same time.

# Notes
I wrote SDF Builder primarily for me, meaning it will be focused on features I found most useful. Of course
I'd be happy to help other people out there use it, so if you have a feature request or find a bug,
do not hesitate to create an issue!
