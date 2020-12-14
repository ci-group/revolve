//
// Created by matteo on 12/10/20.
//

#include "FrameBuffer.h"
#include <string>

using namespace revolve;

cv::Mat FrameBufferRef::to_opencv() const
{
    cv::Mat cv_frame(width, height, CV_MAKETYPE(cv::DataType<float>::type, depth));
    std::memcpy(cv_frame.data, this->buffer, width*height*depth*sizeof(float));

    return cv_frame;
}
