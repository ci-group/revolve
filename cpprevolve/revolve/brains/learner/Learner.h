//
// Created by andi on 25-11-19.
//

#ifndef REVOLVE_LEARNER_H
#define REVOLVE_LEARNER_H

#include "../controller/Controller.h"

namespace revolve
{

    class Learner
    {
    protected:
        std::unique_ptr<revolve::Controller> controller;

    public:

        /// \brief Constructor
        explicit Learner(std::unique_ptr<revolve::Controller> controller)
        : controller(std::move(controller)) {
        }

        /// \brief Deconstructor
        virtual ~Learner() {}

        /// \brief performes the optimization of the controller
        virtual void Optimize() = 0;

        virtual revolve::Controller* getController(){
            return this->controller.get();
        }
    };

}


#endif //REVOLVE_LEARNER_H