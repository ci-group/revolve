//
// Created by andi on 25-11-19.
//

#pragma once

#include <limits>
#include "Evaluator.h"
#include "EvaluationReporter.h"
#include "../controller/Controller.h"

namespace revolve {

class Learner
{
public:
    /// \brief Constructor
    explicit Learner(
            Evaluator *const evaluator,
            EvaluationReporter *const reporter,
            const double evaluation_time,
            const unsigned int n_evaluations)
        : evaluation_time(evaluation_time)
        , end_controller_time(-std::numeric_limits<double>::infinity())
        , evaluation_counter(-1)
        , n_evaluations(n_evaluations)
        , evaluator(evaluator)
        , evaluation_reporter(reporter)
    {}

    /// \brief Deconstructor
    virtual ~Learner() = default;

    /// \brief performes the optimization of the controller
    virtual void optimize(double time, double dt);
    virtual void init_first_controller() = 0;
    virtual void init_next_controller() = 0;
    virtual void finalize_current_controller(double fitness) = 0;

    virtual revolve::Controller *controller() = 0;

protected:
    const double evaluation_time;
    double end_controller_time;

    /// \brief Learning iterations counter
    int evaluation_counter;
    /// \brief Max number of learning iterations
    const unsigned int n_evaluations;

    revolve::Evaluator *evaluator;
    revolve::EvaluationReporter *evaluation_reporter;
};

}
