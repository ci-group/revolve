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
    explicit BayesianOptimizer(
            std::unique_ptr <::revolve::Controller> controller,
            std::unique_ptr<::revolve::Evaluator> evaluator,
            double evaluation_time,
            size_t n_learning_evalutions);

    /// \brief Destructor
    ~BayesianOptimizer() = default;

    /// \brief performes the optimization of the controller. Used as a proxy to call the right optimization method
    void optimize(double time, double dt) override;

    Controller *controller() override
    { return this->_controller.get(); }

    /// \brief bookeeping of the fitnensses
    void save_fitness();


public:

    /// \brief parameters for optimization
    struct params;

    /// \brief Dummy function for limbo
    class evaluation_function {
    public:
        explicit evaluation_function(size_t dim_in)
                : _dim_in(dim_in)
        {}    // Number of input dimension (samples.size())
        size_t dim_in() const
        { return _dim_in; }    // number of dimensions of the fitness

        static size_t dim_out()
        { return 1; }

        Eigen::VectorXd operator()(const Eigen::VectorXd &x) const
        {
            Eigen::VectorXd res(1);
            res(0) = 0;
            return res;
        };

    private:
        const size_t _dim_in;
    };

protected:
    std::unique_ptr<::revolve::Controller> _controller;
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

    /// \brief function to turn the controller into a sample
    std::function<Eigen::VectorXd()> vectorize_controller;

    /// \brief function to turn a sample into a controller
    std::function<void(Eigen::VectorXd)> devectorize_controller;

    /// \brief All fitnesses seen so far. Called observations in limbo context
    std::vector< Eigen::VectorXd > observations;

    /// \brief Best fitness seen so far
    double best_fitness = -10.0;

    /// \brief Sample corresponding to best fitness
    Eigen::VectorXd best_sample;
};
}

#endif //REVOLVE_BAYESIANOPTIMIZER_H
