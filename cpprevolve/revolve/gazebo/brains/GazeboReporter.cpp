//
// Created by matteo on 12/5/19.
//

#include "GazeboReporter.h"
#include <gazebo/transport/Node.hh>


revolve::gazebo::GazeboReporter::GazeboReporter(::gazebo::transport::NodePtr &node)
{
    robot_report_publisher = node->Advertise<revolve::msgs::LearningRobotStates>(
            "~/revolve/robot_reports", 500);
}

void revolve::gazebo::GazeboReporter::report(unsigned int id, unsigned int eval, bool dead, float fitness)
{

}