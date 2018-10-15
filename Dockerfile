FROM cigroup/gazebo:gazebo6-revolve

# Dependencies
RUN apt-get update
RUN apt-get install -y build-essential      \
                       cmake                \
                       cppcheck             \
                       doxygen              \
                       git                  \
                       gsl-bin libgsl0-dev  \
                       mercurial            \
                       python               \
                       python-pip           \
                       xsltproc

ADD . /revolve
RUN /revolve/docker/build_revolve.sh
