//
// Created by matteo on 12/5/19.
//

#include "GazeboReporter.h"
#include <gazebo/msgs/msgs.hh>
#include <gazebo/transport/Node.hh>
#include <revolve/msgs/robot_states_learning.pb.h>

using namespace revolve::gazebo;


GazeboReporter::GazeboReporter(const std::string id, ::gazebo::transport::NodePtr &node)
    : EvaluationReporter(std::move(id))
    , last_eval(-1)
{
    robot_report_publisher = node->Advertise<revolve::msgs::LearningRobotStates>(
            "~/revolve/robot_reports", 500);
    message.set_id(robot_id);
}

void GazeboReporter::report(const unsigned int eval, const bool dead, const double fitness)
{
    const std::lock_guard<std::mutex> lock(message_mutex);
    // construct protobuf message
    message.set_eval(eval);
    message.set_dead(dead);
    message.set_fitness(fitness);
    // behaviour is already collected in `simulation_update`

    // send msgs to Gazebo in python
    this->robot_report_publisher->Publish(message);

    if (last_eval != eval) {
        // Clear behaviour data
        message.mutable_behaviour()->clear_path();

        // this is removed for performance reasons
        //message.clear_behaviour();
        //message.clear_fitness();
        //message.clear_dead();
        //message.clear_eval();

        last_eval = eval;
    }
}


void GazeboReporter::simulation_update(const ignition::math::Pose3d &pose,
                                       double time,
                                       double _step)
{
    const std::lock_guard<std::mutex> lock(message_mutex);
    ::gazebo::msgs::Pose *pose_msg = message.mutable_behaviour()->add_path();
    ::gazebo::msgs::Set(pose_msg, pose);
}
