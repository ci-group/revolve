#pragma once

#include <gazebo/physics/Model.hh>
#include "revolve/brains/controller/sensors/AngleToTargetDetector.h"

namespace revolve {
namespace gazebo {

class GZAngleToTargetDetector : public revolve::AngleToTargetDetector {
public:
    explicit GZAngleToTargetDetector(::gazebo::physics::ModelPtr  robot, const ignition::math::Vector3d& target);
    ~GZAngleToTargetDetector() override = default;

    float detect_angle() override;

protected:
    void get_image(cv::Mat &image) override {
        throw std::runtime_error("Should never call this");
    }

protected:
    const ::gazebo::physics::ModelPtr robot;
    const ignition::math::Vector3d target;
};

}
}