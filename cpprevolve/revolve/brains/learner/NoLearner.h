//
// Created by matteo on 11/22/19.
//
#pragma once

#include <memory>
#include "Learner.h"
#include "../controller/DifferentialCPG.h"

namespace revolve {

template<class ControllerType>
class NoLearner : public Learner
{
public:
    explicit NoLearner(std::unique_ptr<Controller> controller)
            : Learner(nullptr)
            , _controller(std::move(controller))
    {}

    // This is inspired from the GNU `std::make_unique` source code
    template<typename... _Args>
    NoLearner(_Args &&... args)
            : Learner(nullptr)
            , _controller(new ControllerType(std::forward<_Args>(args)...))
    {}

    void optimize(double time, double dt) override
    {}

    Controller *controller() override
    { return this->_controller.get(); }

protected:
    std::unique_ptr<Controller> _controller;
};

}
