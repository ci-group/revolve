//
// Created by matteo on 12/10/20.
//

#ifndef REVOLVE_FRAMEBUFFER_H
#define REVOLVE_FRAMEBUFFER_H

#include <opencv2/opencv.hpp>

namespace revolve {

//class FrameBuffer {
//public:
//    FrameBuffer();
//    ~FrameBuffer() = default;
//};

class FrameBufferRef {
public:
    FrameBufferRef(const void *buffer, unsigned short width, unsigned short height, unsigned short depth)
        : buffer(buffer)
        , width(width)
        , height(height)
        , depth(depth)
    {}
    ~FrameBufferRef() = default;

    cv::Mat to_opencv() const;

private:
    const void *buffer;
    const unsigned short width;
    const unsigned short height;
    const unsigned short depth;
};

}


#endif //REVOLVE_FRAMEBUFFER_H
