//
// Created by matteo on 12/5/19.
//

#pragma once

#include <mutex>
#include <revolve/brains/learner/EvaluationReporter.h>
#include <gazebo/common/Time.hh>
#include <gazebo/transport/TransportTypes.hh>
#include <ignition/math/Pose3.hh>
#include <revolve/msgs/robot_states_learning.pb.h>

namespace revolve {
namespace gazebo {

class GazeboReporter : public EvaluationReporter
{
public:
    explicit GazeboReporter(std::string id, ::gazebo::transport::NodePtr &node);
    ~GazeboReporter() override = default;

    /// \brief Sends proto message to python in gazebo
    void report(unsigned int eval, bool dead, double fitness) override;

    void simulation_update(const ignition::math::Pose3d &pose,
                           const ::gazebo::common::Time &time,
                           double step);

private:
    ::gazebo::transport::PublisherPtr robot_report_publisher;
    ::revolve::msgs::LearningRobotStates message;

    std::mutex message_mutex;
    long last_eval;
};

}
}
