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

# Instalation

For the details, see [wiki pages](https://github.com/ci-group/revolve/wiki).
