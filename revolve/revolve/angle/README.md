# Revolve.Angle
Revolve.Angle is the more opinionated part of revolve that can be used to quickly
scaffold a robot experiment. Hereto it specifies a full robot genome with
the following properties:

- The genome is a tree, with a root node. No cycles (like the Revolve body space).
- Each node of the tree corresponds to a body part. Additionally, each node
  has a number of hidden neurons and neural connections.
- Neural connections do not point to specific nodes - rather they encode a
  path, type and offset. Following the path through the tree leads to
  a different node, where the type and offset specify a neuron. When
  evolving the robot this might thus point connections to different
  locations, or connections might no longer exist at all.

Using Revolve.Angle, robot trees can be generated and evolved using crossover
and mutation. Each robot tree can be converted to a Protobuf Robot object
(see `cpp/msgs/robot.proto`), which can then be turned into SDF and used
for simulation.

Revolve.Angle is opinionated in that it forces the use of a neural network
in combination with the Revolve body tree structure. The user is still
free to choose what types of body parts and neurons are used.

Revolve.Angle is still very much a work in progress.