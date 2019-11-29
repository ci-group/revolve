//
// Created by matteo on 14/06/19.
//

#include <eigen3/Eigen/Core>

#include "BayesianOptimizer.h"
#include "../controller/DifferentialCPG.h"
#include "../controller/Controller.h"

using namespace revolve;

revolve::BayesianOptimizer::BayesianOptimizer(std::unique_ptr<revolve::DifferentialCPG> controller, std::unique_ptr<Evaluator> evaluator)
        : Learner(std::move(evaluator))
        , evaluation_time(15)
        , evaluation_end_time(-1)
        , n_learning_iterations(50)
        , controller(std::move(controller))
{
    this->n_init_samples = 1;
    //this->init_method = "LHS";
    this->kernel_noise = 0.00000001;
    this->kernel_optimize_noise = "false";
    this->kernel_sigma_sq = 0.222;
    this->kernel_l = 0.55;
    this->kernel_squared_exp_ard_k = 4;
    this->acqui_gpucb_delta = 0.5;
    this->acqui_ucb_alpha = 0.44;
    this->acqui_ei_jitter = 0;
    this->acquisition_function = "UCB";

    if (typeid(this->controller) == typeid(std::unique_ptr<revolve::DifferentialCPG>)) {
        devectorize_controller = [this](Eigen::VectorXd weights) {
            //revolve::DifferentialCPG *controller = dynamic_cast<::revolve::DifferentialCPG *>( this->getController());
            //std::vector<double> &controller_weights = controller->loadedWeights;
            //
            //Eigen::VectorXd eigen_weights(weights.size());
            //for (size_t j = 0; j < controller_weights.size(); j++) {
            //    controller_weights.at(j) = weights(j);
            //}

            //TODO controller->load_weights()
        };

        vectorize_controller = [this]() {
            revolve::DifferentialCPG *controller = dynamic_cast<::revolve::DifferentialCPG *>( this->getController());
            const std::vector<double> &weights = controller->loadedWeights;

            // std::vector -> Eigen::Vector
            Eigen::VectorXd eigen_weights(weights.size());
            for (size_t j = 0; j < weights.size(); j++) {
                eigen_weights(j) = weights.at(j);
            }

            return eigen_weights;
        };
    } else {
        throw std::runtime_error("Controller not supported");
    }
}

BayesianOptimizer::~BayesianOptimizer()
{}

void BayesianOptimizer::optimize(double current_time, double dt)
{
    if (current_time < evaluation_end_time) return;

    if (samples.empty())
    {
        assert(n_init_samples == 1 and "INIT SAMPLES > 1 not supported");

        // Save these weights
        this->samples.push_back(this->vectorize_controller());
        this->current_iteration = 0;
    }
    else // next eval
    {
        //TODO DifferentialCPG::bo_step()
        /*boptimizer.optimize(DifferentialCPG::evaluation_function(18),
                            this->samples,
                            this->observations);
        Eigen::VectorXd x = boptimizer.last_sample();
        this->samples.push_back(x);

        this->devectorize_controller(x);*/
        
    }

    // wait for next evaluation
    this->evaluation_end_time = current_time + evaluation_time;
    // Reset Evaluator
    this->evaluator->reset();
}