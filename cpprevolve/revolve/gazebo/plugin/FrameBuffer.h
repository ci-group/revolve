//
// Created by matteo on 12/10/20.
//

#ifndef REVOLVE_FRAMEBUFFER_H
#define REVOLVE_FRAMEBUFFER_H

#include <opencv2/opencv.hpp>
#include <OgrePixelFormat.h>

namespace revolve {

class FrameBuffer {
public:
    FrameBuffer(const void *buffer, unsigned short width, unsigned short height, unsigned short depth);
    ~FrameBuffer() = default;

    const cv::Mat &to_opencv() const;

private:
    cv::Mat cv_frame;
};

class FrameBufferRef {
public:
    FrameBufferRef(const void *buffer, unsigned short width, unsigned short height, unsigned short depth, Ogre::PixelFormat)
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
