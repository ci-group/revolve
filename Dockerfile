FROM ubuntu:bionic

# Dependencies
RUN apt-get update && \
    apt-get install -y build-essential      \
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
                       python3-pip          \
                       libyaml-cpp-dev      \
                       xsltproc             \
                       libcairo2-dev        \
                       graphviz             \
                       libgazebo9-dev       \
                       gazebo9           && \
    apt-get clean  && \
    rm -rf /var/lib/apt/lists/*

ADD . /revolve
RUN /revolve/docker/build_revolve.sh
