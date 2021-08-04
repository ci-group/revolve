//
// Created by matteo on 12/10/20.
//

#include "VideoFileStream.h"
#include <sstream>

using namespace revolve;

VideoFileStream::VideoFileStream(const char *filename, double fps, cv::Size frame_size)
    //    : video(filename, cv::VideoWriter::fourcc('V','P','9','0'), fps, std::move(frame_size), true)
    : video(filename, CV_FOURCC('h', '2', '6', '4'), fps, std::move(frame_size), true), filename(filename)
{
    if (!video.isOpened())
    {
        std::ostringstream error_message;
        error_message << "Could not open video file \"" << filename << "\" for writing";
        throw std::runtime_error(error_message.str());
    }
}

VideoFileStream::~VideoFileStream()
{
    video.release();
}

VideoFileStream &VideoFileStream::operator<<(const cv::Mat &framebuffer)
{
    video << framebuffer;
    return *this;
}

VideoFileStream &VideoFileStream::operator<<(const FrameBuffer &frame)
{
    return (*this) << frame.to_opencv();
}

VideoFileStream &VideoFileStream::operator<<(const FrameBufferRef frame)
{
    cv::Mat framebuffer = frame.to_opencv();
    return (*this) << framebuffer;
}
