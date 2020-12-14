//
// Created by matteo on 12/10/20.
//

#include "VideoFileStream.h"
#include <sstream>

using namespace revolve;

VideoFileStream::VideoFileStream(const char *filename, double fps, cv::Size frame_size)
    : video(filename, cv::VideoWriter::fourcc('v','p','9','0'), fps, frame_size, true)
{
    if (!video.isOpened()) {
        std::ostringstream error_message;
        error_message << "Could not open video file \"" << filename << "\" for writing";
        throw std::runtime_error(error_message.str());
    }
}

VideoFileStream::~VideoFileStream()
{
    video.release();
}

VideoFileStream &VideoFileStream::operator<<(const FrameBufferRef frame)
{
    video.write(frame.to_opencv());
    return *this;
}

