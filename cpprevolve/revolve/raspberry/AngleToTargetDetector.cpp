//
// Created by matteo on 2/28/20.
//

#include "AngleToTargetDetector.h"
#include <iostream>
#include <opencv2/imgproc/imgproc.hpp>

using namespace revolve::raspberry;

AngleToTargetDetector::AngleToTargetDetector(int camera_index, unsigned int shrink_factor, bool show_image)
    : ::revolve::AngleToTargetDetector(shrink_factor, show_image)
    , camera(nullptr)
    , usb_camera(nullptr)
{
    if (camera_index == -1) {
        camera = new raspicam::RaspiCam_Cv();
        if (not camera->open())
            throw std::runtime_error("Error opening the raspberry camera");
    } else {
        usb_camera = new cv::VideoCapture(camera_index);
        if (not usb_camera->isOpened())
            throw std::runtime_error("Error opening the usb camera at index " + std::to_string(camera_index));
    }
}

AngleToTargetDetector::~AngleToTargetDetector()
{
    delete camera;
    delete usb_camera;
}

void AngleToTargetDetector::get_image(cv::Mat &raw_image)
{
    bool result = false;

    if (camera) {
        result = camera->grab();
        camera->retrieve(raw_image);
    } else if (usb_camera) {
        result = usb_camera->read(raw_image);
    } else {
        throw std::runtime_error("Camera device not found");
    }

    if (not result or raw_image.empty()) {
        throw std::runtime_error("Error! could not capture image from the camera");
    }
}

float AngleToTargetDetector::detect_angle()
{
    float angle = ::revolve::AngleToTargetDetector::detect_angle();
    std::cout << "Detected angle: " << angle << std::endl;
    return angle;
}
