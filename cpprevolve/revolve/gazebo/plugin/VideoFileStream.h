//
// Created by matteo on 12/10/20.
//

#ifndef REVOLVE_VIDEOFILESTREAM_H
#define REVOLVE_VIDEOFILESTREAM_H

#include "FrameBuffer.h"
#include <opencv2/opencv.hpp>

namespace revolve {

class VideoFileStream {
public:
    VideoFileStream(const char *filename, double fps, cv::Size frameSize);
    ~VideoFileStream();

    VideoFileStream& operator<<(const cv::Mat &frame);
    VideoFileStream& operator<<(const FrameBuffer &frame);
    VideoFileStream& operator<<(const FrameBufferRef frame);

private:
    cv::VideoWriter video;
    const std::string filename;
};

}

#endif //REVOLVE_VIDEOFILESTREAM_H
