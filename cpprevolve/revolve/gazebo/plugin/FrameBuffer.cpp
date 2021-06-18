//
// Created by matteo on 12/10/20.
//

#include "FrameBuffer.h"
#include <string>

using namespace revolve;

FrameBuffer::FrameBuffer(const void *buffer, unsigned short width, unsigned short height, unsigned short depth)
    : cv_frame(height, width, CV_8UC3) //CV_MAKETYPE(cv::DataType<signed char>::type, depth))
{
    std::memcpy(cv_frame.data, buffer, width*height*depth*sizeof(signed char));
}

const cv::Mat& FrameBuffer::to_opencv() const
{
    cv::cvtColor(cv_frame, cv_frame, cv::COLOR_BGR2RGB);
    return cv_frame;
}


cv::Mat FrameBufferRef::to_opencv() const
{
    int type = CV_MAKETYPE(cv::DataType<char>::type, depth);
    // Original image should be R8G8B8
    cv::Mat cv_frame(height, width, type);
//    cv::cvtColor(cv_frame, cv_frame, cv::COLOR_RGB2BGR);
    std::memcpy(cv_frame.data, this->buffer, width*height*depth*sizeof(char));

    return cv_frame;
}