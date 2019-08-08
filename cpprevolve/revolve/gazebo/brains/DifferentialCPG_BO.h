//
// Created by maarten on 03/02/19.
//

#ifndef REVOLVE_BOPTIMIZER_CPG_H
#define REVOLVE_BOPTIMIZER_CPG_H

// Standard libraries
#include <algorithm>
#include <iostream>
#include <iterator>
#include <sys/time.h>

// External libraries
#include <boost/parameter/aux_/void.hpp>
#include <Eigen/Core>
#include <limbo/bayes_opt/bo_base.hpp>
#include <limbo/tools/macros.hpp>
#include <limbo/tools/random_generator.hpp>
#include <limbo/opt/nlopt_no_grad.hpp>

namespace limbo {
    namespace defaults {
        struct bayes_opt_boptimizer {
            BO_PARAM(int, hp_period, -1);
        };
    }
    BOOST_PARAMETER_TEMPLATE_KEYWORD(acquiopt)

    namespace bayes_opt {

        using boptimizer_signature = boost::parameter::parameters<boost::parameter::optional<tag::acquiopt>,
                boost::parameter::optional<tag::statsfun>,
                boost::parameter::optional<tag::initfun>,
                boost::parameter::optional<tag::acquifun>,
                boost::parameter::optional<tag::stopcrit>,
                boost::parameter::optional<tag::modelfun>>;

        // clang-format off
        /**
        The classic Bayesian optimization algorithm.

        \rst
        References: :cite:`brochu2010tutorial,Mockus2013`
        \endrst

        This class takes the same template parameters as BoBase. It adds:
        \rst
        +---------------------+------------+----------+---------------+
        |type                 |typedef     | argument | default       |
        +=====================+============+==========+===============+
        |acqui. optimizer     |acquiopt_t  | acquiopt | see below     |
        +---------------------+------------+----------+---------------+
        \endrst

        The default value of acqui_opt_t is:
        - ``opt::NLOptNoGrad<Params, nlopt::GN_DIRECT_L_RAND>`` if NLOpt was found in `waf configure`
        - ``opt::Cmaes<Params>`` if libcmaes was found but NLOpt was not found
        - ``opt::GridSearch<Params>`` otherwise (please do not use this: the algorithm will not work as expected!)
        */
        template <class Params,
                class A1 = boost::parameter::void_,
                class A2 = boost::parameter::void_,
                class A3 = boost::parameter::void_,
                class A4 = boost::parameter::void_,
                class A5 = boost::parameter::void_,
                class A6 = boost::parameter::void_>
        // clang-format on
        class BOptimizer : public BoBase<Params, A1, A2, A3, A4, A5, A6> {
        public:
            // defaults
            struct defaults {
                using acquiopt_t = opt::NLOptNoGrad<Params, nlopt::GN_DIRECT_L_RAND>;
            };

            /// link to the corresponding BoBase (useful for typedefs)
            using base_t = BoBase<Params, A1, A2, A3, A4, A5, A6>;
            using model_t = typename base_t::model_t;
            using acquisition_function_t = typename base_t::acquisition_function_t;

            // extract the types
            using args = typename boptimizer_signature::bind<A1, A2, A3, A4, A5, A6>::type;
            using acqui_optimizer_t = typename boost::parameter::binding<args, tag::acquiopt, typename defaults::acquiopt_t>::type;

            /// The main function (run the Bayesian optimization algorithm)
            template <typename StateFunction, typename AggregatorFunction = FirstElem>
            void optimize(const StateFunction& sfun, std::vector<Eigen::VectorXd> all_samples, std::vector<Eigen::VectorXd> all_observations, const AggregatorFunction& afun = AggregatorFunction(), bool reset = true)
            {
                this->_init(sfun, afun, reset); //reset

                // Maarten: set observations and samples
                this->_samples = all_samples;
                this->_observations = all_observations;

                if (!this->_observations.empty()) {
                    _model.compute(this->_samples, this->_observations);
                }
                else {
                    std::cout << "OBSERVATION SET IS EMPTY \n";
                    _model = model_t(StateFunction::dim_in(), StateFunction::dim_out());
                }
                acqui_optimizer_t acqui_optimizer;

                struct timeval timeStart, timeEnd;
                double timeDiff;

                while (!this->_stop(*this, afun)) {

                    gettimeofday(&timeStart,NULL);

                    acquisition_function_t acqui(_model, this->_current_iteration);

                    auto acqui_optimization =
                            [&](const Eigen::VectorXd& x, bool g) { return acqui(x, afun, g); };
                    Eigen::VectorXd starting_point = tools::random_vector(StateFunction::dim_in(), Params::bayes_opt_bobase::bounded());

                    // new samples are from the acquisition optimizer
                    Eigen::VectorXd new_sample = acqui_optimizer(acqui_optimization, starting_point, Params::bayes_opt_bobase::bounded());

                    ///Evaluate a sample and add the result to the 'database'(sample/observations vectors)--it does not update the model
                    this->eval_and_add(sfun, new_sample);

                    this->_update_stats(*this, afun);

                    _model.add_sample(this->_samples.back(), this->_observations.back());

                    if (Params::bayes_opt_boptimizer::hp_period() > 0
                        && (this->_current_iteration + 1) % Params::bayes_opt_boptimizer::hp_period() == 0)
                        _model.optimize_hyperparams();

                    this->_current_iteration++;
                    this->_total_iterations++;

                    gettimeofday(&timeEnd,NULL);

                    timeDiff = 1000000 * (timeEnd.tv_sec - timeStart.tv_sec)
                               + timeEnd.tv_usec - timeStart.tv_usec; //tv_sec: value of second, tv_usec: value of microsecond
                    timeDiff/=1000;

                    std::ofstream ctime;
                    ctime.open("../ctime.txt", std::ios::app);
                    ctime << std::fixed << timeDiff << std::endl;
                }
            }

            /// return the best observation so far (i.e. max(f(x)))
            template <typename AggregatorFunction = FirstElem>
            const Eigen::VectorXd& best_observation(const AggregatorFunction& afun = AggregatorFunction()) const
            {
                auto rewards = std::vector<double>(this->_observations.size());
                std::transform(this->_observations.begin(), this->_observations.end(), rewards.begin(), afun);
                auto max_e = std::max_element(rewards.begin(), rewards.end());
                return this->_observations[std::distance(rewards.begin(), max_e)];
            }

            /// return the best sample so far (i.e. the argmax(f(x)))
            template <typename AggregatorFunction = FirstElem>
            const Eigen::VectorXd& best_sample(const AggregatorFunction& afun = AggregatorFunction()) const
            {
                auto rewards = std::vector<double>(this->_observations.size());
                std::transform(this->_observations.begin(), this->_observations.end(), rewards.begin(), afun);
                auto max_e = std::max_element(rewards.begin(), rewards.end());
                return this->_samples[std::distance(rewards.begin(), max_e)];
            }

            /// Return a reference to the last sample. Used for implementation with revolve
            const Eigen::VectorXd& last_sample(){
                return this->_samples.back();
            }

            const model_t& model() const { return _model; }

        protected:
            model_t _model;
        };

        namespace _default_hp {
            template <typename Params>
            using model_t = model::GPOpt<Params>;
            template <typename Params>
            using acqui_t = acqui::UCB<Params, model_t<Params>>;
        }

        /// A shortcut for a BOptimizer with UCB + GPOpt
        /// The acquisition function and the model CANNOT be tuned (use BOptimizer for this)
        template <class Params,
                class A1 = boost::parameter::void_,
                class A2 = boost::parameter::void_,
                class A3 = boost::parameter::void_,
                class A4 = boost::parameter::void_>
        using BOptimizerHPOpt = BOptimizer<Params, modelfun<_default_hp::model_t<Params>>, acquifun<_default_hp::acqui_t<Params>>, A1, A2, A3, A4>;
    }
}

#endif //REVOLVE_BOPTIMIZER_CPG_H
