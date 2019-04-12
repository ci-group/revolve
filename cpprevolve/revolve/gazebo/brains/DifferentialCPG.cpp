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
    const std::vector< revolve::gazebo::MotorPtr > &_motors,
    const std::vector< revolve::gazebo::SensorPtr > &_sensors)
    : nextState_(nullptr)
    , input_(new double[_sensors.size()])
    , output_(new double[_motors.size()])
{
  // Create transport node
  this->node_.reset(new gz::transport::Node());
  this->node_->Init();

  // Get Robot
  this->robot_ = _model;
  this->nMotors = _motors.size();
  auto name = _model->GetName();

  if (not _settings->HasElement("rv:brain"))
  {
    std::cerr << "No robot brain detected, this is probably an error."
              << std::endl;
    throw std::runtime_error("DifferentialCPG brain did not receive settings");
  }

  std::cout << _settings->GetDescription() << std::endl;
  // TODO: Make this more neat
  auto motor = _settings->GetElement("rv:brain")->GetElement("rv:actuators")->HasElement("rv:servomotor")
               ? _settings->GetElement("rv:brain")->GetElement("rv:actuators")->GetElement("rv:servomotor")
               : sdf::ElementPtr();
  while(motor)
  {
    if (not motor->HasAttribute("coordinates"))
    {
      std::cerr << "Missing required motor coordinates" << std::endl;
      throw std::runtime_error("Robot brain error");
    }

    // Split string and get coordinates
    auto coordinateString = motor->GetAttribute("coordinates")->GetAsString();
    std::vector<std::string> coordinates;
    boost::split(coordinates, coordinateString, boost::is_any_of(";"));

    // Pass coordinates
    auto coordX = std::stoi(coordinates[0]);
    auto coordY = std::stoi(coordinates[1]);
    std::cout << "coordX,coordY = " << coordX << "," << coordY << std::endl;
    auto motorId = motor->GetAttribute("part_id")->GetAsString();
    this->positions_[motorId] = {coordX, coordY};

    // TODO: Determine optimization boundaries
    this->rangeLB = 0.f;
    this->rangeUB = 1;

    // Save neurons: bias/gain/state. Make sure initial states are of different sign.
    this->neurons_[{coordX, coordY, 1}] = {0.f, 0.f, -this->initState}; // Neuron A
    this->neurons_[{coordX, coordY, -1}] = {0.f, 0.f, this->initState}; // Neuron B

    // TODO: Add check for duplicate coordinates
    motor = motor->GetNextElement("rv:servomotor");
  }

  // Add connections between neighbouring neurons
  int i = 0;
  for (const auto &position : this->positions_)
  {
    // Get name and x,y-coordinates of all neurons.
    auto name = position.first;
    int x, y; std::tie(x, y) = position.second;

    // Continue to next iteration in case there is already a connection between the 1 and -1 neuron.
    // These checks feel a bit redundant.
    // if A->B connection exists.
    if (this->connections_.count({x, y, 1, x, y, -1}))
    {
      continue;
    }
    // if B->A connection exists:
    if (this->connections_.count({x, y, -1, x, y, 1}))
    {
      continue;
    }

    // Loop over all positions. We call it neighbours, but we still need to check if they are a neighbour.
    for (const auto &neighbour : this->positions_)
    {
      // Get information of this neuron (that we call neighbour).
      int nearX, nearY; std::tie(nearX, nearY) = neighbour.second;

      // If there is a node that is a Moore neighbour, we set it to be a neighbour for their A-nodes.
      // Thus the connections list only contains connections to the A-neighbourhood, and not the
      // A->B and B->A for some node (which makes sense).
      int distX = std::abs(x - nearX);
      int distY = std::abs(y - nearY);

      // TODO: Verify for non-spiders
      if (((distX <=2 and distY == 0) or
           (distY <=2 and distX == 0) or
           (distX == 1 and distY == 1))
          and not (distX == 0 and distY ==0))
      {
        if(std::get<0>(this->connections_[{x, y, 1, nearX, nearY, 1}]) != 1 or
           std::get<0>(this->connections_[{nearX, nearY, 1, x, y, 1}]) != 1){
          std::cout << "New connection at index " << i << ": " << x << ", " << y << ", " << nearX << ", " << nearY << "\n";
          this->connections_[{x, y, 1, nearX, nearY, 1}] = std::make_tuple(1, i);
          this->connections_[{nearX, nearY, 1, x, y, 1}] = std::make_tuple(1, i);
          i++;
        }
      }
    }
  }

  // Create directory for output
  this->directoryName = "output/cpg_bo/";
  this->directoryName += std::to_string(time(0)) + "/";
  std::system(("mkdir -p " + this->directoryName).c_str());

  // Initialise array of neuron states for Update() method
  this->nextState_ = new double[this->neurons_.size()];

  // Initialize BO
  this->BO_init();

  // Get initial weights. This will yield the first sample
  this->SetWeightMatrix();

  // Initiate the cpp Evaluator
  this->evaluator.reset(new Evaluator(this->evaluationRate_));

}

/**
 * Destructor
 */
DifferentialCPG::~DifferentialCPG()
{
  delete[] this->nextState_;
  delete[] this->input_;
  delete[] this->output_;
}

/*
 * Dummy function for limbo
 */
struct DifferentialCPG::evaluationFunction{
  // number of input dimension (samples.size())
  BO_PARAM(size_t, dim_in, 18);

  // number of dimensions of the fitness
  BO_PARAM(size_t, dim_out, 1);

  Eigen::VectorXd operator()(const Eigen::VectorXd &x) const {
    return limbo::tools::make_vector(0);
  };
};

void DifferentialCPG::BO_init(){
  // Parameters
  this->evaluationRate_ = 20.0;
  this->nInitialSamples = 5;

  // Maximum iterations that learning is allowed
  this->maxLearningIterations = 300;
  this->noLearningIterations = 20; // Number of iterations to walk with best controller

  // Controller in the end
  this->rangeLB = -1.f;
  this->rangeUB = 1.f;
  this->initializationMethod = "RS"; // {RS, LHS, ORT}
  this->runAnalytics = false; // Automatically construct plots
  this->fMax = 1.0;

  // We only want to optimize the weights for now.
  this->nWeights = (int)(this->connections_.size()/2) + this->nMotors;
  std::cout << "Number of weights = connections/2 + nMotors are "
            << this->connections_.size()/2
            << " + "
            << this->nMotors
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
  std::cout << "\nSample method: " << this->initializationMethod << ". Initial "
      "samples are: \n";

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

//    if(((log(this->nInitialSamples)/log(4)) % 1.0) != 0){
//      std::cout << "Warning: Initial number of samples is no power of 4 \n";
//    }

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
        initialSample(j) = sample;

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

void DifferentialCPG::saveFitness(){
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

  // Get and save fitness
  this->saveFitness();

  // In case we are done with the initial random sampling. Correct for
  // initial sample taken by. Statement equivalent to !(i < n_samples -1)
  if (this->currentIteration > this->nInitialSamples - 2){
    // Specify bayesian optimizer
    limbo::bayes_opt::BOptimizer<Params,
                                 limbo::initfun<Init_t>,
                                 limbo::modelfun<GP_t>,
                                 limbo::acquifun<Acqui_t>> boptimizer;

    // Optimize. Pass dummy evaluation function and observations .
    boptimizer.optimize(DifferentialCPG::evaluationFunction(),
                        this->samples,
                        this->observations);

    // Get new sample
    x = boptimizer.last_sample();

    // Save this x_hat_star
    this->samples.push_back(x);
  }
}

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

  // Read sensor data and feed the neural network
  unsigned int p = 0;
  for (const auto &sensor : _sensors)
  {
    sensor->Read(this->input_ + p);
    p += sensor->Inputs();
  }

  // Evaluate policy on certain time limit
  if ((_time - this->startTime_) > this->evaluationRate_) {
    // Update position
    this->evaluator->Update(this->robot_->WorldPose());

    // If we are still learning
    if(this->currentIteration < this->nInitialSamples + this->maxLearningIterations){
      // Get new weights
      this->BO_step();

      // Set new weights
      this->SetWeightMatrix();

      if (this->currentIteration < this->nInitialSamples){
        std::cout << "\nEvaluating initial random sample\n";
      }
      else{
        std::cout << "\nI am learning\n";
      }
    }
      // If we are finished learning but are cooling down
    else if((this->currentIteration >= (this->nInitialSamples + this->maxLearningIterations))
            and (this->currentIteration < (this->nInitialSamples + this->maxLearningIterations + this->noLearningIterations))){
      // Only get fitness for updating
      this->saveFitness();
      this->samples.push_back(this->bestSample);
      std::cout << "\nI am cooling down \n";
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
    this->currentIteration += 1;
  }


  this->Step(_time, this->output_);

  // Send new signals to the motors
  p = 0;
  for (const auto &motor: _motors)
  {
    motor->Update(this->output_ + p, _step);
    p += motor->Outputs();
  }
}


/*
 * Make matrix of weights A as defined in dx/dt = Ax.
 * Element (i,j) specifies weight from neuron i to neuron j in the system of ODEs
 */
void DifferentialCPG::SetWeightMatrix(){
  // Initiate new matrix
  std::vector<std::vector<double>> matrix;

  // Fill with zeroes
  for(size_t i =0; i <this->neurons_.size(); i++)
  {
    // Initialize row in matrix with zeros
    std::vector< double > row;
    for (size_t j = 0; j < this->neurons_.size(); j++) row.push_back(0);
    matrix.push_back(row);
  }

  // Process A<->B connections
  int index = 0;
  for(size_t i =0; i <this->neurons_.size(); i++)
  {
    // Get correct index
    int c = 0;
    if (i%2== 0){
      c = i + 1;
    }
    else{
      c = i - 1;
    }

    // Add a/b connection weight: TODO: current->iteration 5 doesn't exist.
    // Over here it should've already contain a BO_step sample
    // here yet.
    index = (int)(i/2);
    auto w  = this->samples.at(this->currentIteration)(index) *
                                                                (this->rangeUB - this->rangeLB) + this->rangeLB;
    matrix[i][c] = w;
    matrix[c][i] = -w;
  }

  // A<->A connections
  index++;
  int k = 0;
  std::vector<std::string> connectionsSeen;


  for (auto const &connection : this->connections_){
    // Get connection information
    int x1, y1, z1, x2, y2, z2;
    std::tie(x1, y1, z1, x2, y2, z2) = connection.first;

    // Find location of the two neurons in this->neurons list
    int l1, l2;
    int c = 0;
    for(auto const &neuron : this->neurons_){
      int x, y, z;
      std::tie(x, y, z) = neuron.first;
      if (x == x1 and y == y1 and z == z1){
        l1 = c;
      }
      else if (x == x2 and y == y2 and z == z2){
        l2 = c;
      }
      // Update counter
      c++;
    }

    // Add connection to seen connections
    if(l1 > l2){
      int l1_old = l1;
      l1 = l2;
      l2 = l1_old;
    }
    std::string connectionString = std::to_string(l1) + "-" + std::to_string(l2);

    // if not in list, add to list
    if(std::find(connectionsSeen.begin(), connectionsSeen.end(), connectionString) == connectionsSeen.end()) {
      connectionsSeen.push_back(connectionString);
    }
      // else continue to next iteration
    else{
      continue;
    }

    // Get weight
    auto w  = this->samples.at(this->currentIteration)(index + k) *
                                                                   (this->rangeUB - this->rangeLB) + this->rangeLB;

    // Set connection in weight matrix
    matrix[l1][l2] = w;
    matrix[l2][l1] = -w;
    k++;
  }

  // Update matrix
  this->weightMatrix = matrix;

  // Set states back to original value that is close to unit circle
  int c = 0;
  for(auto const &neuron : this->neurons_){
    int x, y, z;
    std::tie(x, y, z) = neuron.first;
    if(z == -1){
      this->nextState_[c] = this->initState;
    }
    else{
      this->nextState_[c] = -this->initState;
    }
    c++;
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
  int neuronCount = 0;
  for (const auto &neuron : this->neurons_)
  {
    // Neuron.second accesses the second 3-tuple of a neuron, containing the bias/gain/state.
    double recipientBias, recipientGain, recipientState;
    std::tie(recipientBias, recipientGain, recipientState) = neuron.second;

    // Save for ODE
    this->nextState_[neuronCount] = recipientState;
    neuronCount++;
  }

  // Copy values from nextstate into x for ODEINT
  state_type x(this->neurons_.size());
  for (size_t i = 0; i < this->neurons_.size(); i++){
    x[i] = this->nextState_[i];
  }

  // Stepper. The result is saved in x. Begin time t, time step dt
  double dt = (_time - this->previousTime);
  this->previousTime = _time;

  // Perform one step
  stepper.do_step(
      [this](const state_type &x, state_type &dxdt, double t)
      {
        for(size_t i = 0; i < this->neurons_.size(); i++){
          dxdt[i] = 0;
          for(size_t j = 0; j < this->neurons_.size(); j++)
          {
            dxdt[i] += x[j]*this->weightMatrix[j][i];
          }
        }
      },
      x,
      _time,
      dt);

  // Copy values into nextstate
  for (size_t i = 0; i < this->neurons_.size(); i++){
    this->nextState_[i] = x[i];
  }

  // Loop over all neurons to actually update their states. Note that this is a new outer for loop
  auto i = 0; auto j = 0;
  for (auto &neuron : this->neurons_)
  {
    // Get bias gain and state for this neuron. Note that we don't take the coordinates.
    // However, they are implicit as their order did not change.
    double bias, gain, state;
    std::tie(bias, gain, state) = neuron.second;
    double x, y, z;
    std::tie(x, y, z) = neuron.first;
    neuron.second = {bias, gain, this->nextState_[i]};

    // Should be one, as output should be based on +1 neurons, which are the A neurons
    if (i % 2 == 1)
    {
      // TODO: Add Milan's function here as soon as things are working a bit
      // f(a) = (w_ao*a - bias)*gain

      // Apply saturation formula
      auto x = this->nextState_[i];
      this->output_[j] = this->fMax*((2.0)/(1.0 + std::pow(2.718, -2.0*x/this->fMax)) -1);
      j++;
    }
    ++i;
  }

  // Debugging: Write the neuron outputs and put in plot to see if we're still non-oscillatory.
  // Write parameters to file
  std::ofstream stateFile;
  stateFile.open(this->directoryName + "nextStates.txt", std::ios::app);
  std::ofstream outputFile;
  outputFile.open(this->directoryName + "outputs.txt", std::ios::app);

  for(size_t i = 0; i < this->neurons_.size(); i++){
    stateFile << this->nextState_[i] << ",";
  }

  for(size_t i = 0; i < this->nMotors; i++){
    outputFile << this->output_[i] << ",";
  }

  stateFile << "\n";
  stateFile.close();
  outputFile << "\n";
  outputFile.close();

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

  // Print to files
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
