//
// Created by matteo on 14/06/19.
//

#include <eigen3/Eigen/Core>
#include <limbo/acqui/gp_ucb.hpp>
#include <limbo/acqui/ei.hpp>
#include <limbo/init/lhs.hpp>
#include <typeinfo>
#include <random>
#include "BayesianOptimizer.h"
#include "BoDefinitions.h"
#include "../controller/DifferentialCPG.h"
#include "../controller/Controller.h"

using namespace revolve;

// Copied from the limbo tutorial the BO implementation is based on
using Mean_t = limbo::mean::Data<BayesianOptimizer::params>;
using Init_t = limbo::init::FlexibleLHS<BayesianOptimizer::params>;
using Kernel_t = limbo::kernel::MaternFiveHalves<BayesianOptimizer::params>;
using GP_t = limbo::model::GP<BayesianOptimizer::params, Kernel_t, Mean_t>;

const static Eigen::IOFormat CSVFormat(11, Eigen::DontAlignCols, ", ", ",");
BayesianOptimizer::BayesianOptimizer(
        std::unique_ptr<revolve::Controller> controller,
        Evaluator *evaluator,
        EvaluationReporter *reporter,
        const double evaluation_time,
        const unsigned int n_learning_evaluations,
        const std::string& model_name)
        : Learner(evaluator, reporter, evaluation_time, n_learning_evaluations)
        , _controller(std::move(controller))
        , n_init_samples(50)
        //, init_method("LHS")
        , kernel_noise(0.001)
        , kernel_optimize_noise("false")
        , kernel_sigma_sq(1.0)
        , kernel_l(0.2)
        , kernel_squared_exp_ard_k(3)
        , acqui_gpucb_delta(0.1)
        , acqui_ucb_alpha(3.0)
        , acqui_ei_jitter(0.5)
        , acquisition_function("UCB")
{
    assert(this->_controller && "BayesianOptimizer: passed null controller");
    switch (this->_controller->controller_type)
    {
        case revolve::Controller::DIFFERENTIAL_CPG:
            devectorize_controller = [this](Eigen::VectorXd weights) {
                // Eigen::vector -> std::vector
                std::vector<double> std_weights(weights.size());
                for (size_t j = 0; j < weights.size(); j++) {
                    std_weights[j] = weights(j);
                }

                auto *temp_controller = dynamic_cast<::revolve::DifferentialCPG*>(this->_controller->into_DifferentialCPG());
                temp_controller->set_connection_weights(std_weights);
            };

            vectorize_controller = [this]() {
                auto *controller = dynamic_cast<::revolve::DifferentialCPG*>(this->_controller->into_DifferentialCPG());
                const std::vector<double> &weights = controller->get_connection_weights();

                // std::vector -> Eigen::Vector
                Eigen::VectorXd eigen_weights(weights.size());
                for (size_t j = 0; j < weights.size(); j++) {
                    eigen_weights(j) = weights.at(j);
                }

                return eigen_weights;
            };
            break;
        default:
            std::cerr << "[BO] Controller not supported" << std::endl;
            throw std::runtime_error("[BO] Controller not supported");
    }

    this->output_dir = "./experiments/IMC/output"+model_name;

    std::ifstream fin(this->output_dir+"/fitnesses.txt");
    std::ifstream gin(this->output_dir+"/genotype.log");
    if(fin){ // Continue Learning/test best
        double fitness;
        while (fin >> fitness){
            // Limbo requires fitness value to be of type Eigen::VectorXd
            Eigen::VectorXd observation = Eigen::VectorXd(1);
            observation(0) = fitness;
            // Save fitness to std::vector. This fitness corresponds to the solution of the previous iteration
            this->observations.push_back(observation);
//            std::cout<<fitness<<std::endl;
        }
        std::cout<<"[BO] Fitness loaded!"<<std::endl;

        int n_weights = this->vectorize_controller().size();
        // Initialize Eigen::VectorXd here.
        Eigen::VectorXd init_sample(n_weights);
        std::string genome;
        while (std::getline(gin, genome))
        {
            std::stringstream ss_weight(genome);
            std::string weight;
            int j =0;
            while (std::getline(ss_weight, weight, ','))
            {
                init_sample(j) = stod(weight);
                j++;
            }
            // Save the initialized weights
            this->samples.push_back(init_sample);
        }

        this->evaluation_counter = this->observations.size()-1;
        int best_index = 1;
        for (int i=0; i<this->observations.size(); i++){
            if (this->best_fitness<this->observations[i][0]){
                this->best_fitness = this->observations[i][0];
                this->best_sample = this->samples[i];
                best_index = i;
            }
        }
        std::cout<<"[BO] Observations: "<<this->observations.size()<<" | Samples: "<<this->samples.size()<<std::endl;
        bool test_best = false; // make this parameter
        if(test_best){
            this->observations.clear();
            this->evaluation_counter = -1;

            auto sec_best = this->samples[best_index - 1];
            this->devectorize_controller(sec_best);
            this->samples.clear();
            this->samples.push_back(this->best_sample);
//            this->samples.push_back(sec_best);
            std::cout<<"Retesting sample fitness: "<< this->best_fitness<<std::endl;
            std::ofstream files;
            files.open(this->output_dir+"/fitness_decom.txt", std::ofstream::out | std::ofstream::trunc);
            files.close();
        }
    }
    else{
        std::cout<<"[BO] Create clean fitness/genotype files"<<std::endl;
        std::ofstream files;
        files.open(this->output_dir+"/fitnesses.txt", std::ofstream::out | std::ofstream::trunc);
        files.open(this->output_dir+"/genotype.log", std::ofstream::out | std::ofstream::trunc);
        files.open("../ctime.txt", std::ofstream::out | std::ofstream::trunc);
        files.close();
    }

    this->output_dir = "./experiments/IMC/output"+model_name;

    if(gin){ // Continue Learning
        double fitness;
        while (fin >> fitness){
            // Limbo requires fitness value to be of type Eigen::VectorXd
            Eigen::VectorXd observation = Eigen::VectorXd(1);
            observation(0) = fitness;
            // Save fitness to std::vector. This fitness corresponds to the solution of the previous iteration
            this->observations.push_back(observation);
//            std::cout<<fitness<<std::endl;
        }
        std::cout<<"Fitness loaded!"<<std::endl;

        int n_weights = this->vectorize_controller().size();
        // Initialize Eigen::VectorXd here.
        Eigen::VectorXd init_sample(n_weights);
        std::string genome;
        while (std::getline(gin, genome))
        {
            std::stringstream ss_weight(genome);
            std::string weight;
            int j =0;
            while (std::getline(ss_weight, weight, ','))
            {
                init_sample(j) = stod(weight);
                j++;
            }
            // Save the initialized weights
            this->samples.push_back(init_sample);
        }
        this->evaluation_counter = this->samples.size()-1;
        int best_index = 1;
        for (int i=0; i<fmin(this->observations.size(),500); i++){
            if (this->best_fitness<this->observations[i][0]){
                this->best_fitness = this->observations[i][0];
                this->best_sample = this->samples[i];
                best_index = i;
            }
        }
        std::cout<<"Observations: "<<this->observations.size()<<" | Samples: "<<this->samples.size()<<std::endl;

        bool test_best = false;
        if(test_best){
            this->observations.clear();
            this->evaluation_counter = -1;

            this->devectorize_controller(this->best_sample);
            this->samples.clear();
            this->samples.push_back(this->best_sample);
        }
    }
    else{
        std::ofstream files;
        files.open(this->output_dir+"/fitnesses.txt", std::ofstream::out | std::ofstream::trunc);
        files.open(this->output_dir+"/genotype.log", std::ofstream::out | std::ofstream::trunc);
        files.open("../ctime.txt", std::ofstream::out | std::ofstream::trunc);
        files.close();
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
//    assert(n_init_samples == 1 and "INIT SAMPLES > 1 not supported");
    std::cout<<"Intialization BO algorithm"<<std::endl;
    // Obtain number of weight for LHS
    int n_weights = this->vectorize_controller().size();

    // Initialize Eigen::VectorXd here.
    Eigen::VectorXd init_sample(n_weights);

    // Working variable
    double my_range = 1.f / this->n_init_samples;

    // If we have n dimensions, create n such vectors that we will permute
    std::vector<std::vector<int>> all_dimensions;

    // Fill vectors
    for (size_t i = 0; i < n_weights; i++) {
        std::vector<int> one_dimension;

        // Prepare for vector permutation
        for (size_t j = 0; j < this->n_init_samples; j++) {
            one_dimension.push_back(j);
        }

        // Vector permutation
        std::random_shuffle(one_dimension.begin(), one_dimension.end());

        // Save permuted vector
        all_dimensions.push_back(one_dimension);
    }

    // For all samples
    for (size_t i = 0; i < this->n_init_samples; i++) {

        // For all dimensions
        for (size_t j = 0; j < n_weights; j++) {
            // Take a LHS
            init_sample(j) = all_dimensions.at(j).at(i) * my_range + ((double) rand() / (RAND_MAX)) * my_range;
        }

        // Save the initialized weights
        this->samples.push_back(init_sample);
    }

    if (!this->samples.empty()){
        this->devectorize_controller(this->samples[0]);
    }
}

void BayesianOptimizer::init_next_controller()
{
    std::cout<<"[BO] start update"<<std::endl;
    Eigen::VectorXd x;
    if (this->samples.size()>this->observations.size()){
        x = this->samples[this->observations.size()];
        std::cout<<"Initializing BO with LHS | "<<this->observations.size()+1<<"/"<< this->samples.size()<<std::endl;
    }
    else{
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

        x = boptimizer.last_sample();
        this->samples.push_back(x);
    }

    // load into controller
    this->devectorize_controller(x);
    std::cout << "[BO] end update" <<std::endl;
}

void BayesianOptimizer::finalize_current_controller(double fitness)
{

    if(fitness <= 5e-11){ // when reloading brain this can cause an error
        std::cout<<"Continue experiment"<<std::endl;
        return ;
    }
    // Save connection_weights if it is the best seen so far
    if(fitness > this->best_fitness)
    {
        this->best_fitness = fitness;
        this->best_sample = this->samples.back();
    }

    std::cout<<"[BO] Resulting fitness: "<<fitness<<"/"<< this->best_fitness<<std::endl;
    // Save connection_weights if it is the best seen so far

    // Limbo requires fitness value to be of type Eigen::VectorXd
    Eigen::VectorXd observation(1);
    observation<<fitness;

    // Save fitness to std::vector. This fitness corresponds to the solution of the previous iteration
    this->observations.push_back(observation);

    //        ->GetAttribute("output_directory")->GetAsString();
    //  Write fitness to file
    std::ofstream fitness_file;
    fitness_file.open(this->output_dir+"/fitnesses.txt", std::ios::app);
    fitness_file<< std::setprecision(std::numeric_limits<long double>::digits10 +1)
                << fitness << std::endl;
    fitness_file.close();

    // Write genotype to file
    std::ofstream genolog(this->output_dir+"/genotype.log", std::ios::app);
    if (genolog.is_open())
    {
        genolog << this->samples.back().format(CSVFormat) << std::endl;
        genolog.close();
    }
    genolog.close();
}

void BayesianOptimizer::load_best_controller()
{
    this->devectorize_controller(this->best_sample);
}
