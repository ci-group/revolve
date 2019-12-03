//
// Created by andi on 25-11-19.
//

#ifndef REVOLVE_LEARNER_H
#define REVOLVE_LEARNER_H

#include "../controller/Controller.h"
#include "Evaluator.h"

namespace revolve {

class Learner
{
public:
    /// \brief Constructor
    explicit Learner(std::unique_ptr <Evaluator> evaluator, std::unique_ptr<Controller> controller)
        : evaluator(std::move(evaluator))
        , controller(std::move(controller))
        {}

    /// \brief Deconstructor
    virtual ~Learner() = default;

    /// \brief performes the optimization of the controller
    virtual void optimize(double time, double dt) = 0;

    /// \brief resets the controller of the learner
    void reset(std::unique_ptr<Learner> learner){
        this->evaluator = move(learner->evaluator);
        this->controller = move(learner->controller);
    }

    virtual revolve::Controller *getController()
    {
        return this->controller.get();
    }

    std::unique_ptr <revolve::Evaluator> evaluator;

    /// \brief controller subject to optimization
    std::unique_ptr <revolve::Controller> controller;
};

}


#endif //REVOLVE_LEARNER_H