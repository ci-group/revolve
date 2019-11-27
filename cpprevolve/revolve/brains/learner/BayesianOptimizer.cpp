//
// Created by matteo on 14/06/19.
//

#include <eigen3/Eigen/Core>

#include "BayesianOptimizer.h"
#include "../controller/DifferentialCPG.h"
#include "../controller/Controller.h"

using namespace revolve;

revolve::BayesianOptimizer::BayesianOptimizer(std::unique_ptr<revolve::DifferentialCPG> controller)
: Learner()
, controller(std::move(controller)){
    /*n_init_samples: 50
    init_method: "LHS"
    kernel_noise: 0.00000001
    kernel_optimize_noise: "false"
    kernel_sigma_sq: 0.222
    kernel_l: 0.55
    kernel_squared_exp_ard_k: 4
    acqui_gpucb_delta: 0.5
    acqui_ucb_alpha: 0.44
    acqui_ei_jitter: 0
    acquisition_function: "UCB"*/
}

BayesianOptimizer::~BayesianOptimizer() {}

void BayesianOptimizer::Optimize()
{
    // if (not time pass 15 seconds) return;

    if(typeid(this->controller) == typeid(std::unique_ptr<revolve::DifferentialCPG>))
    {
        this->controller = BayesianOptimizer::OptimizeCPG();
    }
}

std::unique_ptr<revolve::DifferentialCPG> BayesianOptimizer::OptimizeCPG()
{
    revolve::DifferentialCPG* controller = dynamic_cast<revolve::DifferentialCPG*>( this->getController() );
    std::vector< double > weights = controller->loadedWeights;

    // Save weights for brain
    Eigen::VectorXd loaded_brain(weights.size());
    for(size_t j = 0; j < weights.size(); j++)
    {
        loaded_brain(j) = weights.at(j);
    }

    // Save these weights
    this->samples.push_back(loaded_brain);

    // Go directly into cooldown phase: Note we do require that best_sample is filled. Check this
    this->current_iteration = this->n_init_samples + this->n_learning_iterations;

    // Initiate the cpp Evaluator
    this->evaluator.reset(new revolve::RevEvaluator(this->evaluation_rate));
    this->evaluator->directory_name = this->directory_name;
}