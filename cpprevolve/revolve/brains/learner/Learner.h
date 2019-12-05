//
// Created by andi on 25-11-19.
//

#pragma once

#include "../controller/Controller.h"
#include "Evaluator.h"
#include "EvaluationReporter.h"

namespace revolve {

class Learner
{
public:
    /// \brief Constructor
    explicit Learner(Evaluator *evaluator, EvaluationReporter *reporter)
        : evaluator(evaluator)
        , evaluation_reporter(reporter)
        {}

    /// \brief Deconstructor
    virtual ~Learner() = default;

    /// \brief performes the optimization of the controller
    virtual void optimize(double time, double dt) = 0;

    virtual revolve::Controller *controller() = 0;

protected:
    revolve::Evaluator *evaluator;
    revolve::EvaluationReporter *evaluation_reporter;
};

}
