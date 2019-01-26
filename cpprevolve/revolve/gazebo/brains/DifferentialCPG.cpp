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
#include "../motors/Motor.h"
#include "../sensors/Sensor.h"
#include "DifferentialCPG.h"
#include "eigen3/Eigen/Core"
#include <kernel/kernel.hpp>
#include <tools.hpp>

// Macros for limbo
#include "/home/maarten/Documents/nlopt/build/src/api/nlopt.hpp"
#include "bayes_opt/boptimizer.hpp"

// It probably is bad to have two namespaces
namespace gz = gazebo;
using namespace revolve::gazebo;
using namespace limbo;

#ifndef USE_NLOPT
#define USE_NLOPT //installed NLOPTdim_in
#endif

/////////////////////////////////////////////////
DifferentialCPG::DifferentialCPG(
    const ::gazebo::physics::ModelPtr &_model,
    const sdf::ElementPtr _settings,
    const std::vector< revolve::gazebo::MotorPtr > &/*_motors*/,
    const std::vector< revolve::gazebo::SensorPtr > &/*_sensors*/)
    : flipState_(false)
{
  // Create transport node
  this->node_.reset(new gz::transport::Node());
  this->node_->Init();

  // Maarten: Limbo parameters

  // Maarten: Initialize evaluator
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

  std::random_device rd;
  std::mt19937 mt(rd());
  std::normal_distribution< double > dist(0, 0.0002);
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


    // Maarten; Start the evaluator
    //this->evaluator_.reset(new Evaluator(this->evaluationRate_));


}

/////////////////////////////////////////////////
DifferentialCPG::~DifferentialCPG() = default;

/////////////////////////////////////////////////
void DifferentialCPG::Update(
    const std::vector< revolve::gazebo::MotorPtr > &_motors,
    const std::vector< revolve::gazebo::SensorPtr > &_sensors,
    const double _time,
    const double _step)
{
  boost::mutex::scoped_lock lock(this->networkMutex_);

  auto numMotors = _motors.size();

  // Read sensor data and feed the neural network
  unsigned int p = 0;
  for (const auto &sensor : _sensors)
  {
    sensor->Read(&input_[p]);
    p += sensor->Inputs();
  }

  // Call Limbo here to see what's the most promising point?
  // If done, return the weights for the connections
  // Update the connection weights directly afterwards

  // TODO Update diffCPG
  auto *output = new double[numMotors];
  this->Step(_time, output);

  // Send new signals to the motors
  p = 0;
  for (const auto &motor: _motors)
  {
    //std::cout << motor->PartId() << std::endl;
    motor->Update(&output[p], _step);
    p += motor->Outputs();
  }
}

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

void DifferentialCPG::BO(){

    // Get fitness for BO
    auto fitness = this->evaluator_->Fitness();
}



// Make this function here that Limbo calls to evaluate fitness.
// In turn, this function will call Evaluate::
struct eval_func{
    // Set input dimension (only once)
    static constexpr size_t input_size = 10;

    // number of input dimension (x.size())
    BO_PARAM(size_t, dim_in, input_size);

    // number of dimenions of the result (res.size())
    BO_PARAM(size_t, dim_out, 1);

    // the function to be optimized
    Eigen::VectorXd operator()(const Eigen::VectorXd& x) const {
      // NOTE THAT YOU DON'T MAKE A MISTAKE BY PROBING f(x_t), and getting the
      // previous fitness, namely f(x_(t-1))

      // Input dimension for all functions
      size_t dim_in = input_size;

      /********** 2# SCHWEFEL function N Dimensions **************/
        auto xx = x;

        // transfer interval from [0, 1] to [-500, 500]
        for (int i = 0; i < dim_in; i++) {
          xx[i] = 1000. * x[i] - 500.;
          //std::cout<< xx[i] << std::endl;
        }

        double sum = 0.;
        for (size_t i = 0; i < dim_in; i++) {
          sum = sum + xx[i] * sin(sqrt(abs(xx[i])));
        }

        double obj = 418.9829 * dim_in - sum;
        //std::cout << "Objective is" << obj << std::endl;
        return tools::make_vector(-obj); //maximum = 0 with (420.9687, ...,420.9687)     }
    }
};

// Parmameters
struct DifferentialCPG::Params {
    struct bayes_opt_boptimizer : public defaults::bayes_opt_boptimizer {
    };
// depending on which internal optimizer we use, we need to import different parameters
#ifdef USE_NLOPT
    struct opt_nloptnograd : public defaults::opt_nloptnograd {
    };
#elif defined(USE_LIBCMAES)
    struct opt_cmaes : public defaults::opt_cmaes {
    };
#endif

    struct kernel : public defaults::kernel {
        BO_PARAM(double, noise, 0.00000001);

        BO_PARAM(bool, optimize_noise, false);
    };

    struct bayes_opt_bobase : public defaults::bayes_opt_bobase {
        BO_PARAM(bool, stats_enabled, true);

        BO_PARAM(bool, bounded, true); //false
    };
};

