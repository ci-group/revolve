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
            : Learner(nullptr, nullptr, 0, 0) //TODO add report
            , _controller(std::move(controller))
    {}

    // This is inspired from the GNU `std::make_unique` source code
    template<typename... _Args>
    explicit NoLearner(_Args &&... args)
            : Learner(nullptr, nullptr, 0, 0) //TODO add report
            , _controller(new ControllerType(std::forward<_Args>(args)...))
    {}

    void optimize(double /*time*/, double /*dt*/) override {}
    void init_first_controller() override {}
    void init_next_controller() override {}
    void finalize_current_controller(double /*fitness*/) override {}

    Controller *controller() override
    { return this->_controller.get(); }

protected:
    std::unique_ptr<Controller> _controller;
};

}
