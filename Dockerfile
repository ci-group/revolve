FROM ubuntu:xenial

# Dependencies
RUN apt-get update
RUN apt-get install -y build-essential      \
                       cmake                \
                       curl                \
                       cppcheck             \
                       doxygen              \
                       git                  \
                       gsl-bin libgsl0-dev  \
                       mercurial            \
                       python               \
                       python-pip           \
                       xsltproc
RUN apt-get install -y gazebo9

ADD . /revolve
RUN /revolve/docker/build_revolve.sh
