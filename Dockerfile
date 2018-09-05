FROM cigroup/gazebo:gazebo6-revolve

# Dependencies
RUN apt-get install build-essential \
                    cmake           \
                    cppcheck        \
                    xsltproc        \
                    python          \
                    mercurial

ADD . /revolve
RUN /revolve/docker/build_revolve.sh
