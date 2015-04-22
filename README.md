# Revolve - Robot evolution framework
Revolve aims to be a flexible, easy to use robot evolution framework. It is suitable for
robots with a body that can be captured in a tree structure, with a neural network as
a brain. Revolve consists of the following parts:

- A specification, consisting of a building plan for both a robot body and brain. This specification
  describes "what to put where", but you are free to choose the implementation (i.e. body part types
  and neuron types) yourself.
- An evolution toolkit, which can be used to apply evolutionary operators to the robot body and
  brain.
- A "builder" component, which turns the robot specification into a robot in SDF format, which
  can be used in Gazebo.
- C++ classes to be used as a robot brain.

More information is to follow once things are implemented.