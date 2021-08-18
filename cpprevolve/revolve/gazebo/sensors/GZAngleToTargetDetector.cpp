#include "GZAngleToTargetDetector.h"
#include <cmath>
#include <gazebo/physics/Model.hh>
#include <utility>

using namespace revolve::gazebo;

GZAngleToTargetDetector::GZAngleToTargetDetector(::gazebo::physics::ModelPtr robot, const ignition::math::Vector3d &target)
    : robot(std::move(robot)), target(target)
{
    std::cout << "GZAngleToTargetDetector::GZAngleToTargetDetector(" << target << ")" << std::endl;
}

float GZAngleToTargetDetector::detect_angle()
{
    // Get Robot orientation
    const ignition::math::Pose3d robotPose = robot->WorldPose(); // gives position of robot wrt world, Pose3d has position AND orientation
    const ignition::math::Vector3d forward{0, 1, 0};             // Forward vector
    const ignition::math::Pose3d forward_pose(
        robotPose.CoordPositionAdd(forward),
        ignition::math::Quaterniond::Identity); // needs to be calculated every single time (no static const)

    const ignition::math::Vector3d orientation_vec = (forward_pose.Pos() - robotPose.Pos()).Normalized();
    const ignition::math::Vector3d robot_to_target_vec = (this->target - robotPose.Pos()).Normalized();

    // calculate angle from target, flattened onto the x,y plane
    // explained here:
    // https://code-examples.net/en/q/d6a4f5
    const double dot = orientation_vec[0] * robot_to_target_vec[0] + orientation_vec[1] * robot_to_target_vec[1];
    const double det = orientation_vec[0] * robot_to_target_vec[1] - orientation_vec[1] * robot_to_target_vec[0];
    const double angle = std::atan2(det, dot);

    return angle;
}
