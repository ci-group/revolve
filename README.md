# Revolve

The **R**obot **Evolve** Toolkit consists of a set of software
utilities designed to facilitate evolutionary robotics research. It builds
on top of the widely used Gazebo robotics simulator, providing adequate
performance for simulating populations of average sized robots in real time,
specifically with on-line, embodied evolution and artificial life scenarios in
mind. As such it serves as an aid in evolutionary robotics research regarding
the Evolution of Things[1], in which entities evolve in real-time and
real-space. The toolkit is centered around the Revolve Specification, which
assumes a robot body space consisting of basic building blocks that can be
chained together to form a robotic organism. With the tools included, an
abstract representation of such an organism can be conveniently turned into a
format suitable for simulation with Gazebo. Additional utilities provide
monitoring and control over the simulation environment.

[1]: Agoston E. Eiben and Jum E. Smith, "From Evolutionary Computation to the
Evolution of Things". *Nature*, vol. 521, no 7553, pp. 476-482, May 2015 
doi:[10.1038/nature14544](http://www.cs.vu.nl/%7Egusz/papers/2015-From%20evolutionary%20computation%20to%20the%20evolution%20of%20things.pdf)

## Project structure

```
.
├── cmake               # cmake modules
├── res                 # resources
│   ├── genomes             # robot genomes
│   └── worlds              # simulator world files
├── revolve             # core Revolve project
│   ├── cmake               # cmake modules
│   ├── cpp                 # c++ part
│   └── revolve             # python part
└── tol-revolve         # extension module
└── brain               # robot "brain" module
└── mating              # mating server and logic module
└── localisation        # localisation module
└── hal                 # hardware abstraction module
```