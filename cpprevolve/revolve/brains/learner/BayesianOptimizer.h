//
// Created by matteo on 14/06/19.
//

#ifndef REVOLVE_BAYESIANOPTIMIZER_H
#define REVOLVE_BAYESIANOPTIMIZER_H

#include "Learner.h"
#include "../controller/Controller.h"
#include "../controller/DifferentialCPG.h"

namespace revolve {
class BayesianOptimizer : public Learner
{
public:
    /// \brief Constructor
    BayesianOptimizer(std::unique_ptr <revolve::DifferentialCPG> controller, std::unique_ptr<Evaluator> evaluator);

    /// \brief Destructor
    ~BayesianOptimizer();

    /// \brief performes the optimization of the controller. Used as a proxy to call the right optimization method
    void optimize(double time, double dt) override;


    virtual revolve::Controller *getController()
    {
        return this->controller.get();
    }

    /// \brief Do the optimization for a CPG controller
    /// \param optimized CPG brain
    void optimizeCPG(double time, double dt);

protected:
    const double evaluation_time;
    double evaluation_end_time;

    // BO Learner parameters
    double kernel_noise;
    bool kernel_optimize_noise;
    double kernel_sigma_sq;
    double kernel_l;
    int kernel_squared_exp_ard_k;
    double acqui_gpucb_delta;
    double acqui_ucb_alpha;
    double acqui_ei_jitter;

    /// \brief Specifies the acquisition function used
    std::string acquisition_function;

    /// \brief Max number of iterations learning is allowed
    size_t n_learning_iterations;

    /// \brief Number of initial samples
    size_t n_init_samples;

    /// \brief All samples seen so far.
    std::vector <Eigen::VectorXd> samples;

    /// \brief BO attributes
    size_t current_iteration = 0;

    /// \brief controller subject to optimization
    std::unique_ptr <revolve::Controller> controller;

    std::function<Eigen::VectorXd()> vectorize_controller;
    std::function<void(Eigen::VectorXd)> devectorize_controller;
};
}

#endif //REVOLVE_BAYESIANOPTIMIZER_H
