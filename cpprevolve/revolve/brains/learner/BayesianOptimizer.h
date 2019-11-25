//
// Created by matteo on 14/06/19.
//

#ifndef REVOLVE_BAYESIANOPTIMIZER_H
#define REVOLVE_BAYESIANOPTIMIZER_H

#include "Learner.h"
#include "../controller/Controller.h"
#include "../controller/DifferentialCPG.h"

namespace revolve {
    class BayesianOptimizer : public Learner {
    public:
        /// \brief Constructor
        BayesianOptimizer(std::unique_ptr<revolve::DifferentialCPG> controller) ;

        /// \brief Destructor
        ~BayesianOptimizer();

        /// \brief performes the optimization of the controller. Used as a proxy to call the right optimization method
        void Optimize() override;

        /// \brief Do the optimization for a CPG controller
        /// \param optimized CPG brain
        std::unique_ptr<revolve::DifferentialCPG> OptimizeCPG();

    };
}

#endif //REVOLVE_BAYESIANOPTIMIZER_H
