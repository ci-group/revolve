/*
 * Copyright (C) 2015-2018 Vrije Universiteit Amsterdam
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * Description: TODO: <Add brief description about file purpose>
 * Author: Milan Jelisavcic
 * Date: December 29, 2018
 *
 */

// Existing macros from Milan
#include <cstdlib>
#include <map>
#include <tuple>
#include "DifferentialCPG.h"
#include "../motors/Motor.h"
#include "../sensors/Sensor.h"

// Limbo
#include "DifferentialCPG_BO.h"
#include <limbo/model/gp.hpp>
#include <limbo/init/lhs.hpp>
#include <limbo/model/gp.hpp>
#include <limbo/kernel/exp.hpp>
#include <limbo/tools/macros.hpp>
#include <limbo/model/gp.hpp>
#include <limbo/acqui/ucb.hpp>
#include <limbo/acqui/gp_ucb.hpp>
#include <limbo/bayes_opt/bo_base.hpp>
#include <limbo/mean/mean.hpp>

// Macros for limbo are imported via DIfferentialCPG.h
#include "/home/maarten/Dropbox/BO/BO/limbo/opt/nlopt_no_grad.hpp"

// Redo this as soon as you know that everything works
// #include "/src/api/nlopt.hpp" // Fails compiling, worked before
#include "/home/maarten/Documents/nlopt/build/src/api/nlopt.hpp"

// It probably is bad to have two namespaces
namespace gz = gazebo;
using namespace revolve::gazebo;

// Probably not so nice. I will do this differently later
using Mean_t = limbo::mean::Data<DifferentialCPG::Params>;
using Kernel_t = limbo::kernel::Exp<DifferentialCPG::Params>;
using GP_t = limbo::model::GP<DifferentialCPG::Params, Kernel_t, Mean_t>;
using Init_t = limbo::init::LHS<DifferentialCPG::Params>;
using Acqui_t = limbo::acqui::UCB<DifferentialCPG::Params, GP_t>;

#ifndef USE_NLOPT
#define USE_NLOPT //installed NLOPT
#endif

/**
 * Constructor for DifferentialCPG class.
 *
 * @param _model
 * @param _settings
 */
DifferentialCPG::DifferentialCPG(
        const ::gazebo::physics::ModelPtr &_model,
        const sdf::ElementPtr _settings,
        const std::vector< revolve::gazebo::MotorPtr > &/*_motors*/,
        const std::vector< revolve::gazebo::SensorPtr > &/*_sensors*/)
        : flipState_(false)
        , startTime_ (-1)
{
    // Create transport node
    this->node_.reset(new gz::transport::Node());
    this->node_->Init();

    // Initialize evaluator
    this->evaluationRate_ = 30.0;
    this->maxEvaluations_ = 1000;

    auto name = _model->GetName();
    // Listen to network modification requests
//  alterSub_ = node_->Subscribe(
//      "~/" + name + "/modify_diff_cpg", &DifferentialCPG::Modify,
//      this);

//  auto numMotors = _motors.size();
//  auto numSensors = _sensors.size();

    if (not _settings->HasElement("rv:brain"))
    {
        std::cerr << "No robot brain detected, this is probably an error."
                  << std::endl;
        return;
    }

    // Map of ID to motor element
    std::map< std::string, sdf::ElementPtr > motorsMap;

    // Set for tracking all collected inputs/outputs
    std::set< std::string > toProcess;

    auto motor = _settings->HasElement("rv:motor")
                 ? _settings->GetElement("rv:motor")
                 : sdf::ElementPtr();
    while(motor)
    {
        if (not motor->HasAttribute("x") or not motor->HasAttribute("y"))
        {
            std::cerr << "Missing required motor attributes (x- and/or y- coordinate)"
                      << std::endl;
            throw std::runtime_error("Robot brain error");
        }
        auto motorId = motor->GetAttribute("part_id")->GetAsString();
        auto coordX = std::atoi(motor->GetAttribute("x")->GetAsString().c_str());
        auto coordY = std::atoi(motor->GetAttribute("y")->GetAsString().c_str());

        this->positions_[motorId] = {coordX, coordY};
        this->neurons_[{coordX, coordY, 1}] = {1.f, 0.f, 0.f};
        this->neurons_[{coordX, coordY, -1}] = {1.f, 0.f, 0.f};

//    TODO: Add this check
//    if (this->layerMap_.count({x, y}))
//    {
//      std::cerr << "Duplicate motor ID '" << x << "," << y << "'" <<
//      std::endl;
//      throw std::runtime_error("Robot brain error");
//    }

        motor = motor->GetNextElement("rv:motor");
    }

    // Random initialization of neuron connections
    std::random_device rd;
    std::mt19937 mt(rd());
    std::normal_distribution< double > dist(0, 1);
    std::cout << dist(mt) << std::endl;

    // Add connections between neighbouring neurons
    for (const auto &position : this->positions_)
    {
        auto name = position.first;
        int x, y; std::tie(x, y) = position.second;

        if (this->connections_.count({x, y, 1, x, y, -1}))
        {
            continue;
        }
        if (this->connections_.count({x, y, -1, x, y, 1}))
        {
            continue;
        }
        this->connections_[{x, y, 1, x, y, -1}] = dist(mt);
        this->connections_[{x, y, -1, x, y, 1}] = dist(mt);

        for (const auto &neighbour : this->positions_)
        {
            int nearX, nearY; std::tie(nearX, nearY) = neighbour.second;
            if ((x+1) == nearX or (y+1) == nearY or (x-1) == nearX or (y-1) == nearY)
            {
                this->connections_[{x, y, 1, nearX, nearY, 1}] = 1.f;
                this->connections_[{nearX, nearY, 1, x, y, 1}] = 1.f;
            }
        }
    }

    // Initialize BO
    this->BO_init();

    // Initiate the cpp Evaluator
    this->evaluator.reset(new Evaluator(this->evaluationRate_));
}

/*
 * Dummy function for limbo
 */
struct DifferentialCPG::evaluation_function{
    // Set input dimension (only once)
    static constexpr size_t input_size = 10;

    // number of input dimension (x.size())
    BO_PARAM(size_t, dim_in, input_size);

    // number of dimenions of the result (res.size())
    BO_PARAM(size_t, dim_out, 1);

    Eigen::VectorXd operator()(const Eigen::VectorXd &x) const {
        return limbo::tools::make_vector(0);
    };
};


void DifferentialCPG::BO_init(){
    // Parameters
    this->current_iteration = 0;
    this->max_iterations = 100;
    this->initial_samples = 3;
    this->range_lb = -0.5;
    this->range_ub = 2.f;

    // TODO: Temporary: ask milan
    this->n_weights = 10;

    // For all #initial_samples
    for (int i = 0; i < this->initial_samples; i++){
        // Working variable to hold a random number for each weight to be optimized
        Eigen::VectorXd initial_sample(this->n_weights);

        // For all weights
        for (int j = 0; j < this->n_weights; j++) {
            // Generate a random number in [0, 1]. Transform later
            double f = ((double) rand() / (RAND_MAX));

            // Append f to vector
            initial_sample(j) = f;
        }

        // Save vector in samples.
        this->samples.push_back(initial_sample);
    }

}


void DifferentialCPG::BO_step(){
    // Holder for sample
    Eigen::VectorXd x;

    // Get Fitness if we already did an evaluation
    if (this->current_iteration > 0){
        // Get fitness
        double fitness = this->evaluator->Fitness();

        // Verbose
        std::cout << "Iteration number " << this->current_iteration << " has fitness " << fitness << std::endl;

        // Limbo requires fitness value to be of type Eigen::VectorXd
        Eigen::VectorXd observation = Eigen::VectorXd(1);
        observation(0) = fitness;

        // Save fitness to std::vector. This fitness corresponds to the solution of the previous iteration
        this->observations.push_back(observation);
    }

    // In case we are not done with initial random sampling yet
    if (this->current_iteration < this->initial_samples){
        // Take one of the pre-sampled random samples, and update the weights later
        x = this->samples.at(this->current_iteration);
    }
    // In case we are done with the initial random sampling
    else{
        // Specify bayesian optimizer
        limbo::bayes_opt::BOptimizer<Params, limbo::initfun<Init_t>, limbo::modelfun<GP_t>, limbo::acquifun<Acqui_t>> boptimizer;

        // Verbose: print all samples
        for(int i = 0; i < this->current_iteration; i++){
            auto my_vector = this->samples.at(i);
            std::cout << "Sample " << i << " : ";
            for(int j = 0; j < this->n_weights; j++){
                std::cout <<  my_vector(j) << ", ";
            }
            std::cout << " Fitness: " << this->observations.at(i) << std::endl;
        }

        // Optimize. Pass dummy evaluation function and observations .
        boptimizer.optimize(DifferentialCPG::evaluation_function(), this->samples, this->observations);

        // Get new sample
        x = boptimizer.last_sample();

        // Save this x_hat_star
        this->samples.push_back(x);
    }

    // Process new sample
    for(int i=0; i <x.size(); i ++){
        // Transform the weights to the desired interval
        auto xx = x(i)*(this->range_ub - this->range_lb) + this->range_lb;

        // Set the connection weights with xx (ask Milan)


        // Verbose
        std::cout << "x(" << i << ")= " << x(i) << " ;Transformed: " << xx << std::endl;
    }

    // Update counter
    this->current_iteration +=1;
}

/**
 * Destructor
 */
DifferentialCPG::~DifferentialCPG() = default;

/**
 * Callback function that defines the movement of the robot
 *
 * @param _motors
 * @param _sensors
 * @param _time
 * @param _step
 */
void DifferentialCPG::Update(
        const std::vector< revolve::gazebo::MotorPtr > &_motors,
        const std::vector< revolve::gazebo::SensorPtr > &_sensors,
        const double _time,
        const double _step)
{
    // Prevent two threads from accessing the same resource at the same time
    boost::mutex::scoped_lock lock(this->networkMutex_);

    // Define the number of motors used. This
    auto numMotors = _motors.size();

    // Read sensor data and feed the neural network
    unsigned int p = 0;
    for (const auto &sensor : _sensors)
    {
        sensor->Read(&input_[p]);
        p += sensor->Inputs();
    }

    // Evaluate policy on certain time limit
    if ((_time - this->startTime_) > this->evaluationRate_) {
        // Call iteration of BO
        this->BO_step();

        // Evaluation policy here
        this->startTime_ = _time;
        this->evaluator->Reset();
    }

    // I don't know yet what happens here.
    auto *output = new double[numMotors];
    this->Step(_time, output);

    // Send new signals to the motors
    p = 0;
    for (const auto &motor: _motors) {
        //std::cout << motor->PartId() << std::endl;
        motor->Update(&output[p], _step);
        p += motor->Outputs();
    }

}

/**
 * Step function
 *
 * @param _time
 * @param _output
 */
void DifferentialCPG::Step(
        const double _time,
        double *_output)
{
    auto *nextState = new double[this->neurons_.size()];

    auto i = 0;
    for (const auto &neuron : this->neurons_)
    {
        int x, y, z; std::tie(x, y, z) = neuron.first;
        double biasA, gainA, stateA; std::tie(biasA, gainA, stateA) = neuron.second;

        auto inputA = 0.f;
        for (auto const &connection : this->connections_)
        {
            int x1, y1, z1, x2, y2, z2;
            std::tie(x1, y1, z1, x2, y2, z2) = connection.first;
            auto weightBA = connection.second;

            if (x2 == x and y2 == y and z2 == z)
            {
                auto input = std::get<2>(this->neurons_[{x1, y1, z1}]);
                inputA += weightBA * input + biasA;
            }
        }

        nextState[i] = stateA + (inputA * _time);
        ++i;
    }

    i = 0; auto j = 0;
    auto *output = new double[this->neurons_.size() / 2];
    for (auto &neuron : this->neurons_)
    {
        double biasA, gainA, stateA; std::tie(biasA, gainA, stateA) = neuron.second;
        neuron.second = {biasA, gainA, nextState[i]};
        if (i % 2 == 0)
        {
            output[j] = nextState[i];
            j++;
        }
        ++i;
    }
    _output = output;
}


/**
 * Struct that holds the parameters on which BO is called
 */
struct DifferentialCPG::Params{
    struct bayes_opt_boptimizer : public limbo::defaults::bayes_opt_boptimizer {
    };

    // depending on which internal optimizer we use, we need to import different parameters
#ifdef USE_NLOPT
    struct opt_nloptnograd : public limbo::defaults::opt_nloptnograd {
    };
#elif defined(USE_LIBCMAES)
    struct opt_cmaes : public lm::defaults::opt_cmaes {
    };
#endif

    struct kernel : public limbo::defaults::kernel {
        BO_PARAM(double, noise, 0.00000001);

        BO_PARAM(bool, optimize_noise, false);
    };

    struct bayes_opt_bobase : public limbo::defaults::bayes_opt_bobase {
        BO_PARAM(bool, stats_enabled, true);

        BO_PARAM(bool, bounded, true); //false
    };

    // 1 Iteration as we will perform limbo step by step
    struct stop_maxiterations : public limbo::defaults::stop_maxiterations {
        BO_PARAM(int, iterations, 1);
    };

    struct kernel_exp : public limbo::defaults::kernel_exp {
        /// @ingroup kernel_defaults
        BO_PARAM(double, sigma_sq, 0.001);
        BO_PARAM(double, l, 0.2); // the width of the kernel. Note that it assumes equally sized ranges over dimensions
    };

    struct kernel_squared_exp_ard : public limbo::defaults::kernel_squared_exp_ard {
        /// @ingroup kernel_defaults
        BO_PARAM(int, k, 4); // k number of columns used to compute M
        /// @ingroup kernel_defaults
        BO_PARAM(double, sigma_sq, 1); //brochu2010tutorial p.9 without sigma_sq
    };

    struct kernel_maternfivehalves : public limbo::defaults::kernel_maternfivehalves
    {
        BO_PARAM(double, sigma_sq,1.0); //brochu2010tutorial p.9 without sigma_sq
        BO_PARAM(double, l, 0.3); //characteristic length scale
    };

    struct acqui_gpucb : public limbo::defaults::acqui_gpucb {
        //UCB(x) = \mu(x) + \kappa \sigma(x).
        BO_PARAM(double, delta, 0.525); // default delta = 0.1, delta in (0,1) convergence guaranteed
    };

    struct init_lhs : public limbo::defaults::init_lhs{
        BO_PARAM(int, samples, 100);
    };

    struct acqui_ucb : public limbo::defaults::acqui_ucb {
        //UCB(x) = \mu(x) + \alpha \sigma(x). high alpha have high exploration
        //iterations is high, alpha can be low for high accuracy in enough iterations.
        // In contrast, the low iterations should have high alpha for high
        // searching in limited iterations, which guarantee to optimal.
        BO_PARAM(double, alpha, 1.0); // default alpha = 0.5
    };
};
