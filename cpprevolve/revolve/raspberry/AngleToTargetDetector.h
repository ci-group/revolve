//
// Created by matteo on 2/28/20.
//

#ifndef REVOLVE_RASPBERRY_ANGLETOTARGETDETECTOR_H
#define REVOLVE_RASPBERRY_ANGLETOTARGETDETECTOR_H

#include <opencv2/core/core.hpp>
#include <raspicam/raspicam_cv.h>
#include "../brains/controller/sensors/AngleToTargetDetector.h"

namespace revolve {
namespace raspberry {

class AngleToTargetDetector : public ::revolve::AngleToTargetDetector {
public:
    /**
     * @param camera_index pass -1 to load the raspberry camera
     */
    explicit AngleToTargetDetector(int camera_index, unsigned int shrink_factor = 4, bool show_image = false);
    virtual ~AngleToTargetDetector();

public:
    float detect_angle() override;

private:
    void get_image(cv::Mat &image) override;

protected:
    raspicam::RaspiCam_Cv *camera;
    cv::VideoCapture *usb_camera;
};

}
}


#endif // REVOLVE_RASPBERRY_ANGLETOTARGETDETECTOR_H
