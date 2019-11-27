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


        virtual revolve::Controller* getController() {
            return this->controller.get();
        }

        /// \brief Do the optimization for a CPG controller
        /// \param optimized CPG brain
        std::unique_ptr<revolve::DifferentialCPG> OptimizeCPG();

        // BO Learner parameters
    private: double kernel_noise_;
    private: bool kernel_optimize_noise_;
    public: double kernel_sigma_sq_;
    public: double kernel_l_;
    private: int kernel_squared_exp_ard_k_;
    private: double acqui_gpucb_delta_ ;
    public: double acqui_ucb_alpha_;
    private: double acqui_ei_jitter_;

        /// \brief Max number of iterations learning is allowed
    private: size_t n_learning_iterations;

        /// \brief Number of initial samples
    private: size_t n_init_samples;

        /// \brief Cool down period
    private: size_t n_cooldown_iterations;

        /// \brief How to take initial random samples
    private: std::string init_method;

        /// \brief All samples seen so far.
    private: std::vector< Eigen::VectorXd > samples;

        /// \brief BO attributes
    private: size_t current_iteration = 0;

        /// \brief controller subject to optimization
    protected: std::unique_ptr<revolve::Controller> controller;

    private: std::string directory_name;

        /// \brief evaluation rate
    private: double evaluation_rate;

    };
}

#endif //REVOLVE_BAYESIANOPTIMIZER_H
