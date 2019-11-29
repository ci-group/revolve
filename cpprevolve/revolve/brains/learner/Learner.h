//
// Created by andi on 25-11-19.
//

#ifndef REVOLVE_LEARNER_H
#define REVOLVE_LEARNER_H

#include "../controller/Controller.h"
#include "RevEvaluator.h"

namespace revolve
{

    class Learner
    {
    protected: std::unique_ptr<revolve::RevEvaluator> evaluator;

    public:

        /// \brief Constructor
        explicit Learner(){}

        /// \brief Deconstructor
        virtual ~Learner() {}

        /// \brief performes the optimization of the controller
        virtual void Optimize() = 0;

    };

}


#endif //REVOLVE_LEARNER_H