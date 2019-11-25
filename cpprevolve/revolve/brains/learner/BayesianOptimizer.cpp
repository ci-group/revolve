//
// Created by matteo on 14/06/19.
//

#include "BayesianOptimizer.h"
#include "../controller/DifferentialCPG.h"
#include "../controller/Controller.h"

using namespace revolve;

revolve::BayesianOptimizer::BayesianOptimizer(std::unique_ptr<revolve::DifferentialCPG> controller)
: Learner(std::move(controller)){
}

BayesianOptimizer::~BayesianOptimizer() {}

void BayesianOptimizer::Optimize() {
    if(typeid(this->controller) == typeid(std::unique_ptr<revolve::DifferentialCPG>))
    {
        this->controller = BayesianOptimizer::OptimizeCPG();
    }
}

std::unique_ptr<revolve::DifferentialCPG> BayesianOptimizer::OptimizeCPG() {
    // TODO: here goes the optimization code
}