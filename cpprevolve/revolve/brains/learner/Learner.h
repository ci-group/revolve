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
    explicit Learner(std::unique_ptr <Evaluator> evaluator)
        : evaluator(std::move(evaluator))
    {}

    /// \brief Deconstructor
    virtual ~Learner() = default;

    /// \brief performes the optimization of the controller
    virtual void optimize(double time, double dt) = 0;

    /// \brief resets the controller of the learner
    void reset(std::unique_ptr<Learner> learner){
        this->evaluator = move(learner->evaluator);
    }

protected:
    std::unique_ptr <revolve::Evaluator> evaluator;
};

}


#endif //REVOLVE_LEARNER_H