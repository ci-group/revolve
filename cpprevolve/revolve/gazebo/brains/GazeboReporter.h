//
// Created by matteo on 12/5/19.
//

#pragma once

#include <revolve/brains/learner/EvaluationReporter.h>
#include <gazebo/transport/TransportTypes.hh>

namespace revolve {
namespace gazebo {

class GazeboReporter : public EvaluationReporter
{
public:
    explicit GazeboReporter(::gazebo::transport::NodePtr &node);
    virtual ~GazeboReporter() = default;

    void report(unsigned int id, unsigned int eval, bool dead, float fitness) override;

private:
    ::gazebo::transport::PublisherPtr robot_report_publisher;
};

}
}
