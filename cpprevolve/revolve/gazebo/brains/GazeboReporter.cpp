//
// Created by matteo on 12/5/19.
//

#include "GazeboReporter.h"
#include <gazebo/transport/Node.hh>
#include <revolve/msgs/robot_states_learning.pb.h>



revolve::gazebo::GazeboReporter::GazeboReporter(::gazebo::transport::NodePtr &node)
{
    robot_report_publisher = node->Advertise<revolve::msgs::LearningRobotStates>(
            "~/revolve/robot_reports", 500);
}

void revolve::gazebo::GazeboReporter::report(unsigned int id, unsigned int eval, bool dead, float fitness)
{
    // construct protobuf msg
    msgs::LearningRobotStates msg;
    msg.set_id(id);
    msg.set_eval(eval);
    msg.set_dead(dead);
    msg.set_fitness(fitness);
    //TODO: Add behaviour


    // send msgs to Gazebo in python
    this->robot_report_publisher->Publish(msg);

}