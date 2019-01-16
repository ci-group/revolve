FROM ubuntu:bionic

# Dependencies
RUN apt-get update
RUN apt-get install -y build-essential      \
                       libboost-all-dev     \
                       cmake                \
                       curl                 \
                       cppcheck             \
                       doxygen              \
                       git                  \
                       gsl-bin libgsl0-dev  \
                       mercurial            \
                       pkg-config           \
                       python               \
                       python-pip           \
                       xsltproc
RUN apt-get install -y libgazebo9-dev gazebo9 libyaml-cpp-dev

ADD . /revolve
RUN /revolve/docker/build_revolve.sh
