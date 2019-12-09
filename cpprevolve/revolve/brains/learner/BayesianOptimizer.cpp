//
// Created by matteo on 14/06/19.
//

#include <eigen3/Eigen/Core>
#include <limbo/acqui/gp_ucb.hpp>
#include <limbo/acqui/ei.hpp>
#include <limbo/init/lhs.hpp>

#include "BayesianOptimizer.h"
#include "../controller/DifferentialCPG.h"
#include "../controller/Controller.h"
#include "BoDefinitions.h"

using namespace revolve;

// Copied from the limbo tutorial the BO implementation is based on
using Mean_t = limbo::mean::Data<BayesianOptimizer::params>;
using Init_t = limbo::init::FlexibleLHS<BayesianOptimizer::params>;
using Kernel_t = limbo::kernel::MaternFiveHalves<BayesianOptimizer::params>;
using GP_t = limbo::model::GP<BayesianOptimizer::params, Kernel_t, Mean_t>;

BayesianOptimizer::BayesianOptimizer(
        std::unique_ptr<revolve::Controller> controller,
        Evaluator *evaluator,
        EvaluationReporter *reporter,
        const double evaluation_time,
        const unsigned int n_learning_evalutions)
        : Learner(evaluator, reporter, evaluation_time, n_learning_evalutions)
        , _controller(std::move(controller))
        , n_init_samples(1)
        //, init_method("LHS")
        , kernel_noise(0.00000001)
        , kernel_optimize_noise("false")
        , kernel_sigma_sq(0.222)
        , kernel_l(0.55)
        , kernel_squared_exp_ard_k(4)
        , acqui_gpucb_delta(0.5)
        , acqui_ucb_alpha(0.44)
        , acqui_ei_jitter(0.0)
        , acquisition_function("UCB")
{

    if (typeid(this->_controller) == typeid(std::unique_ptr<revolve::DifferentialCPG>)) {
        devectorize_controller = [this](Eigen::VectorXd weights) {
            // Eigen::vector -> std::vector
            std::vector<double> std_weights(weights.size());
            for (size_t j = 0; j < weights.size(); j++) {
                std_weights[j] = weights(j);
            }

            auto *temp_controller = dynamic_cast<::revolve::DifferentialCPG *>(this->_controller.get());
            temp_controller->set_connection_weights(std_weights);
        };

        vectorize_controller = [this]() {
            auto *controller = dynamic_cast<::revolve::DifferentialCPG *>(this->_controller.get());
            const std::vector<double> &weights = controller->get_connection_weights();

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

/**
 * Struct that holds the parameters on which BO is called. This is required
 * by limbo.
 */
struct BayesianOptimizer::params
{

    struct bayes_opt_boptimizer : public limbo::defaults::bayes_opt_boptimizer
    {
    };

    // depending on which internal optimizer we use, we need to import different parameters
#ifdef USE_NLOPT
    struct opt_nloptnograd : public limbo::defaults::opt_nloptnograd {
    };
#elif defined(USE_LIBCMAES)
    struct opt_cmaes : public lm::defaults::opt_cmaes {
    };
#endif

    struct kernel : public limbo::defaults::kernel
    {
        BO_PARAM(double, noise, 0.001);

        BO_PARAM(bool, optimize_noise, false);
    };

    struct bayes_opt_bobase : public limbo::defaults::bayes_opt_bobase
    {
        // set stats_enabled to prevent creating all the directories
        BO_PARAM(bool, stats_enabled, false);

        BO_PARAM(bool, bounded, true);
    };

    // 1 Iteration as we will perform limbo step by steop
    struct stop_maxiterations : public limbo::defaults::stop_maxiterations
    {
        BO_PARAM(int, iterations, 1);
    };

    struct kernel_exp : public limbo::defaults::kernel_exp
    {
        /// @ingroup kernel_defaults
        BO_PARAM(double, sigma_sq, 0.1);

        BO_PARAM(double, l, 0.1); // the width of the kernel. Note that it assumes equally sized ranges over dimensions
    };

    struct kernel_squared_exp_ard : public limbo::defaults::kernel_squared_exp_ard
    {
        /// @ingroup kernel_defaults
        BO_PARAM(int, k, 3); // k number of columns used to compute M
        /// @ingroup kernel_defaults
        BO_PARAM(double, sigma_sq, 0.1); //brochu2010tutorial p.9 without sigma_sq
    };

    struct kernel_maternfivehalves : public limbo::defaults::kernel_maternfivehalves
    {
        BO_DYN_PARAM(double, sigma_sq); //brochu2010tutorial p.9 without sigma_sq
        BO_DYN_PARAM(double, l); //characteristic length scale
    };

    struct acqui_gpucb : public limbo::defaults::acqui_gpucb
    {
        //UCB(x) = \mu(x) + \kappa \sigma(x).
        BO_PARAM(double, delta,
                 0.1);//acqui_gpucb_delta_); // default delta = 0.1, delta in (0,1) convergence guaranteed
    };

    struct acqui_ei : public limbo::defaults::acqui_ei
    {
        BO_PARAM(double, jitter, 0.5);
    };

    // This is just a placeholder to be able to use limbo with revolve
    struct init_lhs : public limbo::defaults::init_lhs
    {
        BO_PARAM(int, samples, 0);
    };

    struct acqui_ucb : public limbo::defaults::acqui_ucb
    {
        //constexpr double ra = acqui_ucb_alpha_;
        //UCB(x) = \mu(x) + \alpha \sigma(x). high alpha have high exploration
        //iterations is high, alpha can be low for high accuracy in enough iterations.
        // In contrast, the lsow iterations should have high alpha for high
        // searching in limited iterations, which guarantee to optimal.
        //        BO_PARAM(double, alpha, transform_double(acqui_ucb_alpha_)); // default alpha = 0.5
        BO_DYN_PARAM(double, alpha); // default alpha = 0.5

    };
};

BO_DECLARE_DYN_PARAM(double, BayesianOptimizer::params::acqui_ucb, alpha);
BO_DECLARE_DYN_PARAM(double, BayesianOptimizer::params::kernel_maternfivehalves, sigma_sq);
BO_DECLARE_DYN_PARAM(double, BayesianOptimizer::params::kernel_maternfivehalves, l);

void BayesianOptimizer::init_first_controller()
{
    assert(n_init_samples == 1 and "INIT SAMPLES > 1 not supported");

    // Save the initial weights
    this->samples.push_back(this->vectorize_controller());
}

void BayesianOptimizer::init_next_controller()
{
    //TODO are these global variables 😱?
    params::acqui_ucb::set_alpha(this->acqui_ucb_alpha);
    params::kernel_maternfivehalves::set_l(this->kernel_l);
    params::kernel_maternfivehalves::set_sigma_sq(this->kernel_sigma_sq);

    // Specify bayesian optimizer. TODO: Make attribute and initialize at bo_init
    limbo::bayes_opt::BOptimizer<params,
            limbo::initfun<Init_t>,
            limbo::modelfun<GP_t>,
            limbo::acquifun<limbo::acqui::UCB<BayesianOptimizer::params, GP_t >>> boptimizer;

    // Optimize. Pass evaluation function and observations .
    boptimizer.optimize(BayesianOptimizer::evaluation_function(this->samples[0].size()),
                        this->samples,
                        this->observations);

    Eigen::VectorXd x = boptimizer.last_sample();
    this->samples.push_back(x);

    // load into controller
    this->devectorize_controller(x);
}

void BayesianOptimizer::finalize_current_controller(double fitness)
{
    // Save connection_weights if it is the best seen so far
    if(fitness > this->best_fitness)
    {
        this->best_fitness = fitness;
        this->best_sample = this->samples.back();
    }

    // Limbo requires fitness value to be of type Eigen::VectorXd
    Eigen::VectorXd observation = Eigen::VectorXd(1);
    observation(0) = fitness;

    // Save fitness to std::vector. This fitness corresponds to the solution of the previous iteration
    this->observations.push_back(observation);
}
