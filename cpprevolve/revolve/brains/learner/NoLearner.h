//
// Created by matteo on 11/22/19.
//
#ifndef REVOLVE_NOLEARNER_H
#define REVOLVE_NOLEARNER_H
#include <memory>

#include "Learner.h"
#include "../controller/DifferentialCPG.h"

namespace revolve {
template<class ControllerType>
class NoLearner : public Learner
{
public:
    NoLearner(std::unique_ptr<Controller> controller)
            : controller(std::move(controller))
    {}    // This is inspired from the GNU `std::make_unique` source code
    template<typename... _Args>
    NoLearner(_Args &&... args)
            : controller(new ControllerType(std::forward<_Args>(args)...))
    {}

    void optimize(double time, double dt) override;

    ::revolve::Controller *getController()
    {
        return this->controller.get();
    }

private:
    std::unique_ptr<Controller> controller;
};
}
#endif //REVOLVE_NOLEARNER_H