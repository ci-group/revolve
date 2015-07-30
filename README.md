# Revolve - Robot evolution framework
Revolve aims to be a flexible robot evolution framework, providing C++ and Python libraries to create,
simulate and manage robots in the Gazebo robot simulator.

## Robot body framework
The most elaborate component of Revolve is the robot body framework. It is heavily inspired by the
robot structure als employed by [Robogen](http://www.robogen.org). The framework works by specifying 
a body space using a `revolve.spec.BodyImplementation`. This boils down to specifying a number of predefined
 body parts, each of which defines a number of inputs 
(i.e. sensors), outputs (i.e. motors) and attachment slots, which are locations where other
body parts connect. Parts can also specify any number of configurable numeric parameters.
A body part is physically represented by a subclass of the `revolve.build.sdf.BodyPart` class, 
and can in turn consist of many components that give
the part its physical behavior. These components are specified using the classes in the `sdfbuilder`
library, which is a thin convenience wrapper over SDF itself (direct XML can also be used with little effort).

Given a specification, a robot body can be constructed by Revolve from a `revolve.spec.msgs.Body` class,
which is specified in Google Protobuf for flexibility. This class specifies a tree structure, starting
with a root node extending to other body parts through its attachment slots.  A `revolve.build.sdf.BodyBuilder`
class is capable of turning a combination of such a robot and a body specification into an SDF file
that can be directly used in Gazebo.

Revolve also ships with some simple generator classes, which can generate arbitrary robot bodies from scratch
given a set of constraints.

## Robot brains
Of course you would like your robot to also have a brain. Revolve also ships with a specification for a simple
neural network, with its interface based on a robot body if desired.
 
## Gazebo plugins
Revolve also comes with a number of Gazebo plugins to power the defined components in simulation. The `RobotController`
C++ class is a solid basis for controlling a robot in a simple manner, providing default implementations of
 motor controllers and sensor readers with an interface over the body parts' inputs and outputs.
 
## Revolve.Angle
The most complete, but opinionated part of Revolve is Angle, which is a framework that allows specification, generation
and evolution of robots that fit within the defined body space and have a neural network as a brain. See the information
in the `revolve.angle` folder for details.
 
## Work in progress
I am writing revolve, as well as the related library [sdfbuilder](https://github.com/ElteHupkes/sdf-builder) as part
of my Master's thesis research. The actual code that is going to be running my experiments is currently being
constructed in my [Triangle of Life repository](https://github.com/ElteHupkes/tol-revolve). This repo also serves
as the currently only and therefore best way to see Revolve in action. All of this is still very much a work in
progress, though I do have large parts of Revolve and ToL working at this point.