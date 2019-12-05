//
// Created by matteo on 12/5/19.
//

#pragma once

#include <revolve/brains/learner/EvaluationReporter.h>

namespace revolve {
namespace gazebo {

class GazeboReporter : public EvaluationReporter
{
public:
    explicit GazeboReporter();
    virtual ~GazeboReporter() = default;

    void report(unsigned int id, unsigned int eval, bool dead, float fitness) override;
};

}
}
