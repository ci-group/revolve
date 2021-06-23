#include "GZAngleToTargetDetector.h"
#include <cmath>
#include <gazebo/physics/Model.hh>
#include <utility>

using namespace revolve::gazebo;

GZAngleToTargetDetector::GZAngleToTargetDetector(::gazebo::physics::ModelPtr robot, const ignition::math::Vector3d& target)
    : robot(std::move(robot))
    , target(target)
{
    std::cout << "GZAngleToTargetDetector::GZAngleToTargetDetector()" << std::endl;
}

float GZAngleToTargetDetector::detect_angle()
 {
    // Get Robot orientation
    const ignition::math::Pose3d robotPose = robot->WorldPose(); // gives position of robot wrt world, Pose3d has position AND orientation
    const ignition::math::Vector3d forward { 0 , -1, 0}; // Forward vector
    const ignition::math::Pose3d forward_pose (
        robotPose.CoordPositionAdd(forward),
        ignition::math::Quaterniond::Identity
        );  // needs to be calculated every single time (no static const)
    const ignition::math::Vector3d &forward_vec = forward_pose.Pos(); // x, y, z; point one unit forward from the robot
    const ignition::math::Vector3d orientation_vec = forward_pose.Pos() - robotPose.Pos(); // x, y, z, robot orientation

    // calculate angle from target

    // Forward x and y
    const double x_f = forward_vec[0];
    const double y_f = forward_vec[1];

    // Target x and y
    const double x_t = this->target[0];
    const double y_t = this->target[1];

    const double angle_robot_forward = std::atan2(y_f, x_f);
    const double angle_robot_target = std::atan2(y_t, x_t);
    const double angle = angle_robot_forward - angle_robot_target;

//    std::cout << "Detected angle to target: " << angle << std::endl;

    return angle;
}