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
    explicit Learner(std::unique_ptr <Evaluator> evaluator, std::unique_ptr<EvaluationReporter> reporter)
        : evaluator(std::move(evaluator))
        , evaluation_reporter(std::move(reporter))
        {}

    /// \brief Deconstructor
    virtual ~Learner() = default;

    /// \brief performes the optimization of the controller
    virtual void optimize(double time, double dt) = 0;

    virtual revolve::Controller *controller() = 0;

protected:
    std::unique_ptr <revolve::Evaluator> evaluator;
    std::unique_ptr <revolve::EvaluationReporter> evaluation_reporter;
};

}
