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
#ifndef USE_NLOPT
#define USE_NLOPT
#endif

// STL macros
#include <cstdlib>
#include <map>
#include <algorithm>
#include <random>
#include <tuple>
#include <time.h>

// Other libraries
#include <limbo/acqui/ucb.hpp>
#include <limbo/acqui/gp_ucb.hpp>
#include <limbo/bayes_opt/bo_base.hpp>
#include <limbo/init/lhs.hpp>
#include <limbo/kernel/exp.hpp>
#include <limbo/model/gp.hpp>
#include <limbo/mean/mean.hpp>
#include <limbo/tools/macros.hpp>
#include <limbo/opt/nlopt_no_grad.hpp>

// Project headers
#include "../motors/Motor.h"

#include "../sensors/Sensor.h"

#include "DifferentialCPG.h"

#include "DifferentialCPG_BO.h"

// Define namespaces
namespace gz = gazebo;
using namespace revolve::gazebo;

// Probably not so nice
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
  this->robot_ = _model;
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
  std::uniform_real_distribution< double > dist(0, 1);
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
struct DifferentialCPG::evaluationFunction{
  // number of input dimension (samples.size())
  BO_PARAM(size_t, dim_in, 14);

  // number of dimenions of the fitness
  BO_PARAM(size_t, dim_out, 1);

  Eigen::VectorXd operator()(const Eigen::VectorXd &x) const {
    return limbo::tools::make_vector(0);
  };
};

void DifferentialCPG::BO_init(){
  // Parameters
  this->evaluationRate_ = 120.0;
  this->currentIteration = 0;
  this->nInitialSamples = 14;
  // Maximum iterations that learning is allowed
  this->maxLearningIterations = 300;
  this->noLearningIterations = 20; // Number of iterations to walk with best
  // controller in the end
  this->rangeLB = 0.f;
  this->rangeUB = 1.f;
  this->initializationMethod = "LHS"; // {RS, LHS, ORT}
  this->runAnalytics = true; // Automatically construct plots
  this->fMax = 1.0;
  // We only want to optimize the weights for now. Maybe later we can do
  // bias/gain.
  this->nWeights = this->connections_.size();
  std::cout << "Number of connections (hence weights) are "
            << this->nWeights
            << std::endl;


  /*
  // Limbo BO Parameters
  this->alpha = 0.5; // Acqui_UCB. Default 0.5
  this->delta = 0.3; // Acqui GP-UCB. Default 0.1. Convergence guaranteed in (0,1)
  this->l = 0.2; // Kernel width. Assumes equally sized ranges over dimensions
  this->sigma_sq = 0.001; // Kernel variance. 0.001 recommended
  this->k = 4; // EXP-ARD kernel. Number of columns used to compute M.
  */


  // Information purposes
  std::cout << "Sample method: " << this->initializationMethod << std::endl;

  // Random sampling
  if(this->initializationMethod == "RS") {
    for (size_t i = 0; i < this->nInitialSamples; i++) {
      // Working variable to hold a random number for each weight to be optimized
      Eigen::VectorXd initialSample(this->nWeights);

      // For all weights
      for (int j = 0; j < this->nWeights; j++) {
        // Generate a random number in [0, 1]. Transform later
        double f = ((double) rand() / (RAND_MAX));

        // Append f to vector
        initialSample(j) = f;
      }

      // Save vector in samples.
      this->samples.push_back(initialSample);

      for(int k = 0; k < initialSample.size(); k ++){
        std::cout << initialSample(k) << ", ";
      }
      std::cout << "\n";

    }
  }
    // Latin Hypercube Sampling
  else if(this->initializationMethod == "LHS"){
    // Check
    if(this->nInitialSamples % this->nWeights != 0){
      std::cout << "Warning: Ideally the number of initial samples is a multiple of nWeights for LHS sampling \n";
    }

    // Working variables
    double myRange = 1.f/this->nInitialSamples;

    // If we have n dimensions, create n such vectors that we will permute
    std::vector<std::vector<int>> allDimensions;

    // Fill vectors
    for (int i=0; i < this->nWeights; i++){
      std::vector<int> oneDimension;

      // Prepare for vector permutation
      for (size_t j = 0; j < this->nInitialSamples; j++){
        oneDimension.push_back(j);
      }

      // Vector permutation
      std::random_shuffle(oneDimension.begin(), oneDimension.end() );

      // Save permuted vector
      allDimensions.push_back(oneDimension);
    }

    // For all samples
    for (size_t i = 0; i < this->nInitialSamples; i++){
      // Initialize Eigen::VectorXd here.
      Eigen::VectorXd initialSample(this->nWeights);

      // For all dimensions
      for (int j = 0; j < this->nWeights; j++){
        // Take a LHS
        initialSample(j) = allDimensions.at(j).at(i)*myRange + ((double) rand() / (RAND_MAX))*myRange;
      }

      // Append sample to samples
      this->samples.push_back(initialSample);

      for(int k = 0; k < initialSample.size(); k ++){
        std::cout << initialSample(k) << ", ";
      }
      std::cout << "\n";
    }
  }

  else if(this->initializationMethod == "ORT"){
    // Set the number of blocks per dimension
    int nBlocks = (int)(log(this->nInitialSamples)/log(4));

    // Working variables
    double myRange = 1.f/this->nInitialSamples;


    //if(((log(this->nInitialSamples)/log(4)) % 1.0) != 0){
    //  std::cout << "Warning: Initial number of samples is no power of 4 \n";
    //}


    // Initiate for each  dimension a vector holding a permutation of 1,...,nInitialSamples
    std::vector<std::vector<int>> allDimensions;
    for (int i = 0; i < this->nWeights; i++) {
      // Holder for one dimension
      std::vector<int> oneDimension;
      for (size_t j = 0; j < this->nInitialSamples; j++) {
        oneDimension.push_back(j);
      }

      // Do permutation
      std::random_shuffle(oneDimension.begin(), oneDimension.end() );

      // Save to list
      allDimensions.push_back(oneDimension);
    }

    // Draw nInitialSamples
    for (size_t i = 0; i < this->nInitialSamples; i++) {
      // Initiate new sample
      Eigen::VectorXd initialSample(this->nWeights);

      // Each dimensions will have 2^nBlocks rows it can choose from
      std::vector<int> rowsInBlock;
      int end = (int)(std::pow(2, nBlocks));

      // Loop over all the blocks: we don't have to pick a block randomly
      for (int j =0; j < nBlocks; j++) {
        // Generate row numbers in this block: THIS IS WRONG
        for(int k = j*end; k < (j+1)*end; k++)
        {
          rowsInBlock.push_back(k);
        }
        // Take the vector that is pointing to the actual vector
        std::vector<int> *rowNumbers = &allDimensions.at(j);

        // Get set intersection
        std::vector<int> availableRows;
        std::set_intersection(
            rowsInBlock.begin(),
            rowsInBlock.end(),
            rowNumbers->begin(),
            rowNumbers->end(),
            std::back_inserter(availableRows));

        // Shuffle availableRows
        auto rng = std::default_random_engine {};
        std::shuffle(std::begin(availableRows), std::end(availableRows), rng);

        // Draw the sample
        double sample = myRange*availableRows.at(0) + ((double) rand() /
                                                       (RAND_MAX))*myRange;
        initialSample(j) = sample; // This is wrong

        // Remove element from the list with available row numbers
        std::vector<int>::iterator position = std::find(availableRows.begin(),
                                                        availableRows.end(),
                                                        availableRows.at(0));

        if (position != availableRows.end())
        {
          availableRows.erase(position);
        }
      }

      // Append sample to samples
      this->samples.push_back(initialSample);

      // Print sample
      for (int h = 0; h < initialSample.size(); h++){
        std::cout << initialSample(h) << ", ";
      }
      std::cout << std::endl;

    }
  }

}

void DifferentialCPG::getFitness(){
  // Get fitness
  double fitness = this->evaluator->Fitness();

  // Save sample if it is the best seen so far
  if(fitness >this->bestFitness){
    this->bestFitness = fitness;
    this->bestSample = this->samples.back();
  }

  // Verbose
  std::cout << "Iteration number " << this->currentIteration << " has fitness " << fitness << std::endl;

  // Limbo requires fitness value to be of type Eigen::VectorXd
  Eigen::VectorXd observation = Eigen::VectorXd(1);
  observation(0) = fitness;

  // Save fitness to std::vector. This fitness corresponds to the solution of the previous iteration
  this->observations.push_back(observation);
}

void DifferentialCPG::BO_step(){
  // Holder for sample
  Eigen::VectorXd x;

  // Get Fitness if we already did an evaluation
  if (this->currentIteration > 0){
    // Get fitness
    this->getFitness();
  }

  // In case we are not done with initial random sampling yet
  if (this->currentIteration < this->nInitialSamples){
    // Take one of the pre-sampled random samples, and update the weights later
    x = this->samples.at(this->currentIteration);
  }
    // In case we are done with the initial random sampling
  else{
    // Specify bayesian optimizer
    limbo::bayes_opt::BOptimizer<Params, limbo::initfun<Init_t>, limbo::modelfun<GP_t>, limbo::acquifun<Acqui_t>> boptimizer;

    // Optimize. Pass dummy evaluation function and observations .
    boptimizer.optimize(DifferentialCPG::evaluationFunction(),
                        this->samples, this->observations);

    // Get new sample
    x = boptimizer.last_sample();

    // Save this x_hat_star
    this->samples.push_back(x);
  }

  // Update counter
  this->currentIteration +=1;
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
    // Update position
    this->evaluator->Update(this->robot_->WorldPose());
    /*
    std::cout << "XYZ: ";
    std::cout << this->currPosition_.Pos().X() << ", ";
    std::cout << this->currPosition_.Pos().Y() << ", ";
    std::cout << this->currPosition_.Pos().Z() << "\n";
    */
    // If we are still learning
    if(this->currentIteration < (this->nInitialSamples + this->maxLearningIterations)){
      this->BO_step();
      std::cout << "I am learning \n";
    }
      // If we are finished learning but are cooling down
    else if((this->currentIteration >= (this->nInitialSamples + this->maxLearningIterations))
            and (this->currentIteration < (this->nInitialSamples + this->maxLearningIterations + this->noLearningIterations))){
      // Only get fitness for updating
      this->getFitness();
      this->samples.push_back(this->bestSample);
      this->currentIteration += 1;
      std::cout << "I am cooling down \n";
    }
      // Else we don't want to update anything, but save data from this run once.
    else if(this->runAnalytics) {
      this->getAnalytics();
      this->runAnalytics = false;
      std::cout << "I am finished \n";
    }

    // Evaluation policy here
    this->startTime_ = _time;
    this->evaluator->Reset();
  }

  // I don't know yet what happens here.
  double *output = new double[numMotors];
  /*
  std::cout << "cp1 \n";
  for(int n; n < numMotors; n++){
    std::cout << output[n] << ", ";
  }
  std::cout << "\n";
  */
  this->Step(_time, output); // SOMETHIGN GOES WRONG HERE, AS CP1 IS FINE,
  // BUT CP2 IS NOT
  //std::cout << "cp2 \n";
  /*
  for(int n; n < numMotors; n++){
    std::cout << output[n] << ", ";
  }
  std::cout << "\n";
  */
  // Send new signals to the motors
  p = 0;
  for (const auto &motor: _motors) {
    motor->Update(&output[p], _step);
    p += motor->Outputs();
    //std::cout << "Signal is " << output[p] << "\n";
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
    biasA = 0;
    gainA = 1;
    //std::cout << "Bias/Gain/State: " <<biasA << ", " << gainA << ", " <<
    //stateA << "\n";

    auto inputA = 0.f;
    for (auto const &connection : this->connections_)
    {
      int x1, y1, z1, x2, y2, z2;
      std::tie(x1, y1, z1, x2, y2, z2) = connection.first;

      //auto weightBA = connection.second;
      // When we are still learning
      auto weightBA = this->samples.back()(i) * (this->rangeUB - this->rangeLB) + this->rangeLB;

      // TODO: replace. If we are finished learning, take best sample seen so far
      if(this->currentIteration >= this->maxLearningIterations + this->nInitialSamples) {
        weightBA = this->bestSample(i) * (this->rangeUB - this->rangeLB) + this->rangeLB;
      }


      if (x2 == x and y2 == y and z2 == z)
      {
        // INPUT IS ALWAYS 0, which is where the error is
        // Access last element in the tuple
        //auto input = std::get<0>(this->neurons_[{x1, y1, z1}]);
        /*
        std::cout << "cp5: Input x is " << std::get<0>(this->neurons_[{x1, y1, z1}]) << std::endl;
        std::cout << "cp5: Input y is " << std::get<1>(this->neurons_[{x1,y1,
                                                                       z1}]) << std::endl;
        std::cout << "cp5: Input z is " << std::get<2>(this->neurons_[{x1,
                                                                       y1, z1}]) << std::endl;
        */
        // Get new x position for CPG input
        auto input = this->robot_->WorldPose().Pos().X();
        //std::cout << "cp5 " << input << std::endl;
        //std::cout << "Input is " << input << "\n";
        // inputA += weightBA * input + biasA
        inputA += (weightBA * input - biasA)*gainA;
      }
    }

    //std::cout << "Time is " << _time << std::endl;

    nextState[i] = stateA + (inputA * _time);
    // std::cout << "Nextstate[i] is " << nextState[i] <<std::endl;

    ++i;
  }

  i = 0; auto j = 0;
  auto *output = new double[this->neurons_.size() / 2];

  //std::cout << "c3: Lenght of output: " << this->neurons_.size() << std::endl;

  for (auto &neuron : this->neurons_)
  {
    double biasA, gainA, stateA; std::tie(biasA, gainA, stateA) = neuron.second;
    neuron.second = {biasA, gainA, nextState[i]};
    if (i % 2 == 0)
    {
      // Apply saturation formula
      auto x = nextState[i];
      output[j] = this->fMax*((2.0)/(1.0 + std::pow(2.718, -2.0*x/this->fMax))
                              -1);
      //std::cout << j << ": " << output[j] << std::endl;
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
    // set stats_enabled to prevent creating all the directories
    BO_PARAM(bool, stats_enabled, false);

    BO_PARAM(bool, bounded, true);
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
    BO_PARAM(double, sigma_sq, 0.001); //brochu2010tutorial p.9 without sigma_sq
  };

  struct kernel_maternfivehalves : public limbo::defaults::kernel_maternfivehalves
  {
    BO_PARAM(double, sigma_sq, 0.001); //brochu2010tutorial p.9 without sigma_sq
    BO_PARAM(double, l, 0.2); //characteristic length scale
  };

  struct acqui_gpucb : public limbo::defaults::acqui_gpucb {
    //UCB(x) = \mu(x) + \kappa \sigma(x).
    BO_PARAM(double, delta, 0.1); // default delta = 0.1, delta in (0,1) convergence guaranteed
  };

  // We do Random Sampling manually to allow for incorporation in our loop
  struct init_lhs : public limbo::defaults::init_lhs{
    BO_PARAM(int, samples, 0);
  };

  struct acqui_ucb : public limbo::defaults::acqui_ucb {
    //UCB(x) = \mu(x) + \alpha \sigma(x). high alpha have high exploration
    //iterations is high, alpha can be low for high accuracy in enough iterations.
    // In contrast, the lsow iterations should have high alpha for high
    // searching in limited iterations, which guarantee to optimal.
    BO_PARAM(double, alpha, 0.5); // default alpha = 0.5
  };
};


void DifferentialCPG::getAnalytics(){
  // Generate directory name
  std::string directoryName = "output/cpg_bo/";
  directoryName += std::to_string(time(0)) + "/";
  std::system(("mkdir -p " + directoryName).c_str());

  // Write parameters to file
  std::ofstream myFile;
  myFile.open(directoryName + "parameters.txt");
  myFile << "Dimensions: " << this->nWeights << "\n";
  // TODO
  //myFile << "Kernel used: " << kernel_used << "\n";
  //myFile << "Acqui. function used: " << acqui_used << "\n";
  //myFile << "Initialization method used: " << initialization_used << "\n";
  myFile << "UCB alpha: " << Params::acqui_ucb::alpha() << "\n";
  myFile << "GP-UCB delta: " << Params::acqui_gpucb::delta() << "\n";
  myFile << "Kernel noise: " << Params::kernel::noise() << "\n";
  myFile << "No. of iterations: " << Params::stop_maxiterations::iterations() << "\n";
  myFile << "EXP Kernel l: " << Params::kernel_exp::l() << "\n";
  myFile << "EXP Kernel sigma_sq: " << Params::kernel_exp::sigma_sq() << "\n";
  myFile << "EXP-ARD Kernel k: "<< Params::kernel_squared_exp_ard::k() << "\n";
  myFile << "EXP-ARD Kernel sigma_sq: "<< Params::kernel_squared_exp_ard::sigma_sq() << "\n";
  myFile << "MFH Kernel sigma_sq: "<< Params::kernel_maternfivehalves::sigma_sq() << "\n";
  myFile << "MFH Kernel l: "<< Params::kernel_maternfivehalves::l() << "\n\n";
  myFile.close();

  // Save data from run
  std::ofstream myObservationsFile;
  myObservationsFile.open(directoryName + "fitnesses.txt");
  std::ofstream mySamplesFile;
  mySamplesFile.open(directoryName + "samples.txt");

  // Print to files: TODO: GET LAST FITNESS AS WELL S.T. WE CAN GET RID OF -1
  for(size_t i = 0; i < (this->observations.size()); i++){
    auto mySample = this->samples.at(i);

    for(int j = 0; j < this->nWeights; j++){
      mySamplesFile << mySample(j) << ", ";
    }
    mySamplesFile << "\n";

    // When the samples are commented out, it works.
    myObservationsFile << this->observations.at(i) << "\n";
  }

  // Close files
  myObservationsFile.close();
  mySamplesFile.close();

  // Call python file to construct plots
  std::string pythonPlotCommand = "python3 experiments/RunAnalysisBO.py "
                                  + directoryName
                                  + " "
                                  + std::to_string((int)this->nInitialSamples)
                                  + " "
                                  + std::to_string((int)this->noLearningIterations);
  std::system(pythonPlotCommand.c_str());

}
