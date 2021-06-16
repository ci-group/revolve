//
// Created by matteo on 2/28/20.
//

#ifndef REVOLVE_ANGLETOTARGETDETECTOR_H
#define REVOLVE_ANGLETOTARGETDETECTOR_H

#include "Sensor.h"
//#include <opencv2/core/core.hpp>

namespace revolve {

class AngleToTargetDetector : public Sensor {
public:
    explicit AngleToTargetDetector(unsigned int shrink_factor = 4, bool show_image = false);
    virtual ~AngleToTargetDetector() = default;

    void read(double *input) override;
    virtual float detect_angle() = 0;

//private:
//    virtual void get_image(cv::Mat &image) = 0;

protected:
    const bool show_image;
    const unsigned int shrink_factor;
    double angle;
//    cv::Mat raw_image, image;
//    cv::Mat image_blur, image_hsv, image_blue, image_green1, image_green2, image_green;
};

}


#endif //REVOLVE_ANGLETOTARGETDETECTOR_H
