
ADD /revolve
RUN mkdir -p build && cd build
RUN cmake ../cpp \
          -DCMAKE_BUILD_TYPE="Release" \
          -DLOCAL_BUILD_DIR=1
    make -j4
