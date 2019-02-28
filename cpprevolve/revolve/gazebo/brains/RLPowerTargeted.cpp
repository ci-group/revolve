/*
* Copyright (C) 2017 Vrije Universiteit Amsterdam
*
* Licensed under the Apache License, Version 2.0 (the "License");
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
* Date: March 28, 2016
*
* TODO: <Remove reset robot (first fix the robot's angle>
*/

#include <fstream>
#include <iostream>
#include <map>
#include <random>
#include <string>
#include <vector>

#include <gsl/gsl_spline.h>

#include "RLPowerTargeted.h"
#include "../motors/Motor.h"
#include "../sensors/Sensor.h"

namespace gz = gazebo;

using namespace revolve::gazebo;

/////////////////////////////////////////////////
RLPower::RLPower(
    const ::gazebo::physics::ModelPtr &_model,
    const ::gazebo::physics::ModelPtr &_goalBox,
    const sdf::ElementPtr &/* _node */,
    const std::vector< MotorPtr > &_motors,
    const std::vector< SensorPtr > &/* _sensors */)
    : generationCounter_(0)
    , cycleStartTime_(-1)
    , startTime_(-1)
{
  //  // Listen to network modification requests
  //  this->alterSub_ = this->node_->Subscribe(
  //      "~/" + _modelName + "/modify_spline_policy", &RLPower::Modify,
  //      this);

  // Controller parameters
  this->setSeed = false;
  this->sourceYSize_ = 3;
  this->eps = 0.2;
  this->phiMin = 2.0;
  this->evaluationRate_ = 60.0;
  this->fastEvaluationRate = 7.5;
  this->numInterpolationPoints_ = 100;
  this->maxEvaluations_ = 6000;
  this->learningPeriod = 20;
  // Learner parameters
  this->algorithmType_ = "D";
  this->maxRankedPolicies_ = 20;
  this->sigma_ = 2.50;
  this->sigmaPolicy = 2.50;
  this->tau_ = 0.2;

  // Working variables for controller
  this->node_.reset(new gz::transport::Node());
  this->node_->Init();
  this->robot_ = _model;
  this->goalBox_ = _goalBox;
  this->goalX = 100;
  this->stepRate_ = this->numInterpolationPoints_ / this->sourceYSize_;
  this->bestFitnessGait = 0;
  this->bestFitnessLeft = 0;
  this->bestFitnessRight = 0;

  // Generate first random policy for controller
  auto numMotors = _motors.size();
  this->InitialisePolicy(numMotors);

  // Initialize: Save best policy
  this->bestPolicyGait = std::make_shared< Policy >(numMotors);
  this->bestPolicyLeft = std::make_shared< Policy >(numMotors);
  this->bestPolicyRight = std::make_shared< Policy >(numMotors);
  this->bestInterpolationCacheGait = std::make_shared< Policy >(numMotors);
  this->bestInterpolationCacheLeft = std::make_shared< Policy >(numMotors);
  this->bestInterpolationCacheRight = std::make_shared< Policy >(numMotors);

  // Initialize policies. Problem must be here
  this->rankedPoliciesGait = std::map< double, PolicyPtr, std::greater< double>>();
  this->rankedPoliciesRight = std::map< double, PolicyPtr, std::greater< double>>();
  this->rankedPoliciesLeft = std::map< double, PolicyPtr, std::greater< double>>();

  // Set seed
  if(this->setSeed){
    srand(1);
  }

  // Start the evaluator
  this->evaluator_.reset(new Evaluator(this->evaluationRate_));
}


void RLPower::SetRandomGoalBox(){
  // Generate end-point for targeted locomotion that is at least 1 unit of distance away
  std::cout << "SetrandomGoalBox \n";

  // Set new position that is sufficiently far away
  while(this->distToObject <= 1.0){
    // Generate new goal points in the neighbourhood of the robot
    this->goalX = ((double) rand() / (RAND_MAX))*3.f - 1.5 + this->evaluator_->currentPosition_.Pos().X();
    this->goalY = ((double) rand() / (RAND_MAX))*3.f - 1.5 + this->evaluator_->currentPosition_.Pos().Y();

    // Check distance
    this->distToObject = std::pow(
        std::pow(this->goalX - this->evaluator_->currentPosition_.Pos().X(), 2) +
        std::pow(this->goalY - this->evaluator_->currentPosition_.Pos().Y(), 2)
        , 0.5);

    std::cout << "Distance is " << this->distToObject << " with points " << this->goalX << ", " << this->goalY << std::endl;
  }

  // Update goal box
  auto newPose = ::ignition::math::Pose3d();
  newPose.Set(goalX, goalY, 0.05, 0.0, 0.0, 0.0);
  this->goalBox_->SetWorldPose(newPose);
}

/////////////////////////////////////////////////
RLPower::~RLPower() = default;

/////////////////////////////////////////////////
void RLPower::Update(
    const std::vector< MotorPtr > &_motors,
    const std::vector< SensorPtr > &/* _sensors */,
    double _time,
    double _step)
{
  if (this->startTime_ < 0)
  {
    this->startTime_ = _time;
  }

  auto numMotors = _motors.size();

  // Evaluate policy on certain time limit
  if ((_time - this->startTime_) > this->evaluationRate_){
    if(this->generationCounter_ < this->maxEvaluations_){
      std::cout << "Iteration: " << this->generationCounter_ << std::endl;

      // Get current position and update it to later obtain fitness
      this->evaluator_->Update(this->robot_->WorldPose());

      // Get distance to object
      this->distToObject = std::pow(
          std::pow(this->goalX - this->evaluator_->currentPosition_.Pos().X(), 2) +
          std::pow(this->goalY - this->evaluator_->currentPosition_.Pos().Y(), 2)
          , 0.5);

      // Debugging
      std::cout << "Distance to goal: " << distToObject << std::endl;

      // Re-initiate target when close enough
      if(this->distToObject < this->eps){
        std::cout << "Object reached \n";
        this->SetRandomGoalBox();
      }

      // Set face:
      if (this->generationCounter_ >= this->maxRankedPolicies_){
        std::cout << "Goal coordinates: " << this->goalX << ", " << this->goalY << std::endl;
        std::cout << "Goal angle: " << this->goalAngle << std::endl;

        // Show angle of goal
        this->goalAngle = this->getVectorAngle(this->evaluator_->currentPosition_.Pos().X(),
                                               this->evaluator_->currentPosition_.Pos().Y(),
                                               this->goalX,
                                               this->goalY,
                                               0.f,
                                               -1.f);
      }

      // Update policy
      this->UpdatePolicy(numMotors);
      this->startTime_ = _time;

      // Set the current as previous position
      this->evaluator_->Reset();
      std::cout << "\n";
    }

    // Initiate goal box
    if(this->generationCounter_ == this->maxRankedPolicies_ + 3*this->learningPeriod + 1){
      this->distToObject = 0.f;
      this->SetRandomGoalBox();

      // Allow for more smooth moving
      this->evaluationRate_ = this->fastEvaluationRate;
    }
  }

  // generate outputs
  auto *output = new double[numMotors];
  this->Output(numMotors, _time, output);

  // Send new signals to the actuators
  auto p = 0;
  for (const auto &motor: _motors)
  {
    motor->Update(&output[p], _step);
    p += motor->Outputs();
  }

  delete[] output;
}

/////////////////////////////////////////////////
void RLPower::InitialisePolicy(size_t _numSplines)
{
  std::random_device rd;
  std::mt19937 mt(rd());
  std::normal_distribution< double > dist(0, this->sigma_);

  // Init first random controller
  if (not this->currentPolicy_)
  {
    this->currentPolicy_ = std::make_shared< Policy >(_numSplines);
  }

  for (size_t i = 0; i < _numSplines; ++i)
  {
    Spline spline(this->sourceYSize_);
    for (size_t j = 0; j < this->sourceYSize_; ++j)
    {
      spline[j] = dist(mt);
    }
    this->currentPolicy_->at(i) = spline;
  }

  // Init of empty cache
  if (not this->interpolationCache_)
  {
    this->interpolationCache_ = std::make_shared< Policy >(_numSplines);
  }

  for (size_t i = 0; i < _numSplines; ++i)
  {
    this->interpolationCache_->at(i).resize(this->numInterpolationPoints_, 0);
  }

  this->InterpolateCubic(
      _numSplines,
      this->currentPolicy_.get(),
      this->interpolationCache_.get());
}

/////////////////////////////////////////////////
void RLPower::InterpolateCubic(
    const size_t _numSplines,
    Policy *const _sourceY,
    Policy *_destinationY)
{
  const auto sourceYSize = (*_sourceY)[0].size();
  const auto destinatioYSize = (*_destinationY)[0].size();

  const auto N = sourceYSize + 1;
  auto *x = new double[N];
  auto *y = new double[N];
  auto *xNew = new double[destinatioYSize];

  auto *acc = gsl_interp_accel_alloc();
  const auto *t = gsl_interp_cspline_periodic;
  auto *spline = gsl_spline_alloc(t, N);

  // init x
  auto step_size = RLPower::CYCLE_LENGTH / sourceYSize;
  for (size_t i = 0; i < N; ++i)
  {
    x[i] = step_size * i;
  }

  // init xNew
  step_size = CYCLE_LENGTH / destinatioYSize;
  for (size_t i = 0; i < destinatioYSize; ++i)
  {
    xNew[i] = step_size * i;
  }

  for (size_t j = 0; j < _numSplines; ++j)
  {
    auto &sourceYLine = _sourceY->at(j);
    auto &destinationYLine = _destinationY->at(j);

    // init y
    // TODO use memcpy
    for (size_t i = 0; i < sourceYSize; ++i)
    {
      y[i] = sourceYLine[i];
    }

    // make last equal to first
    y[N - 1] = y[0];

    gsl_spline_init(spline, x, y, N);

    for (size_t i = 0; i < destinatioYSize; ++i)
    {
      destinationYLine[i] = gsl_spline_eval(spline, xNew[i], acc);
    }
  }

  gsl_spline_free(spline);
  gsl_interp_accel_free(acc);

  delete[] xNew;
  delete[] y;
  delete[] x;
}

// Input: old; new. Function that determines the angle between the resulting vector and the normal [d1_x,d1_y]-vector
double RLPower::getVectorAngle(double p1_x, double p1_y, double p2_x, double p2_y, double d1_x, double d1_y){
  // Get direction vector of input
  double x2 = p2_x - p1_x;
  double y2 = p2_y - p1_y;

  // Normalize
  const double dNorm = std::pow(std::pow(x2,2) + std::pow(y2,2), 0.5);
  x2 = x2/dNorm;
  y2 = y2/dNorm;

  // Get arctan2 input
  double dot = d1_x*x2 + d1_y*y2;
  double det = d1_x*y2 - d1_y*x2;

  // Return angle
  return(std::atan2(det,dot)*180.0/M_PI);
}

void RLPower::UpdatePolicy(const size_t _numSplines)
{
  // Set orientation for next iteration in case we're learning
  size_t n_init = this->maxRankedPolicies_;
  if (this->generationCounter_ < n_init){
    this->moveOrientation = "random";
    std::cout << "Orientation: random\n";
  }
  else if (this->generationCounter_ < n_init + this->learningPeriod){
    if (this->generationCounter_ == n_init){
      this->sigma_ = this->sigmaPolicy;
    }
    this->moveOrientation = "gait";
    std::cout << "Orientation: gait\n";
  }
  else if (this->generationCounter_ < n_init + 2*this->learningPeriod){
    if (this->generationCounter_ == n_init + this->learningPeriod){
      this->sigma_ = this->sigmaPolicy;
    }
    this->moveOrientation = "right";
    std::cout << "Orientation: right\n";
  }
  else if (this->generationCounter_ < n_init + 3*this->learningPeriod){
    if (this->generationCounter_ == n_init + 2*this->learningPeriod){
      this->sigma_ = this->sigmaPolicy;
    }
    this->moveOrientation = "left";
    std::cout << "Orientation: left\n";
  }
    // When we are finished learning
  else{
    // Get angle we will move in under gait sub-brain
    double robot_angle = this->robot_->WorldPose().Rot().Yaw()*180.0/M_PI;
    double move_angle = this->face + robot_angle;

    if(move_angle >=180.0){
      move_angle -= 360;
    }
    else if (move_angle <= -180){
      move_angle += 360;
    }

    double angleDifference = this->goalAngle - move_angle;
    if(angleDifference >180) angleDifference -= 360;
    else if (angleDifference < -180) angleDifference +=360;

    // Calculate angle difference between face and object
    std::cout << "Face angle: " << this->face << std::endl;
    std::cout << "Move angle " << move_angle << std::endl;
    std::cout << "Angle difference is " << angleDifference << std::endl;

    std::cout << "Main brain: Go ";
    if(angleDifference > 180){
      angleDifference  = -(360.f - angleDifference);
    }
    else if(angleDifference < -180){
      angleDifference  = (360.f + angleDifference);
    }

    double objectRadius = 0.05;
    double robotRadius = 0.05;
    double phiSides = atan((robotRadius + objectRadius)/this->distToObject)*180.0/M_PI;

    // Determine the angle.
    if(angleDifference > std::max(this->phiMin, phiSides) and angleDifference > -this->phiMin){
      this->moveOrientation = "left";
      std::cout << "left with controller fitness " << this->bestFitnessLeft << "\n";
    }
    else if (angleDifference < std::min(-this->phiMin, - phiSides)){
      this->moveOrientation = "right";
      std::cout << "right with controller fitness " << this->bestFitnessRight << "\n";
    }
    else{
      this->moveOrientation = "gait";
      std::cout << "gait with controller fitness " << this->bestFitnessGait << "\n";
    }

    std::cout << "phiCorrected is: " << phiSides << std::endl;
  }

  // Update generation counter
  this->generationCounter_++;

  //If we still want to learn, i.e. create a new policy
  if(this->generationCounter_ <= n_init + 3*this->learningPeriod){
    // Calculate fitness for current policy
    auto currentFitnessGait= this->Fitness("gait");
    auto currentFitnessLeft= this->Fitness("left");
    auto currentFitnessRight= this->Fitness("right");

    // Compare with best gait policy
    if (currentFitnessGait > this->bestFitnessGait){
      // Verbose
      std::cout << "Update best policy for gait\n";
      std::cout << "Old face: "<< this->face << "\n";

      // Update face
      double robotMoveAngle = this->getVectorAngle(this->evaluator_->previousPosition_.Pos().X(),
                                        this->evaluator_->previousPosition_.Pos().Y(),
                                        this->evaluator_->currentPosition_.Pos().X(),
                                        this->evaluator_->currentPosition_.Pos().Y(),
                                        0.f,
                                        -1.f);
      double startAngle = this->evaluator_->previousPosition_.Rot().Yaw()*180.0/M_PI;

      this->face = robotMoveAngle - startAngle;
      if(this->face > 180){
        this->face -= 360;
      }
      else if (this->face < -180){
        this->face +=360;
      }

      std::cout << "Start angle " << startAngle << "\n";
      std::cout << "Robot angle " << robotMoveAngle << "\n";
      std::cout << "New face: "<< this->face << "\n";

      // Save this fitness  for future comparison
      this->bestFitnessGait = currentFitnessGait;

      // Save this policy
      *this->bestPolicyGait = *this->currentPolicy_;
      *this->bestInterpolationCacheGait = *this->interpolationCache_;
    }

    // Compare with best left turn policy
    if (currentFitnessLeft > this->bestFitnessLeft){
      // Verbose
      std::cout << "Update best policy for left turn \n";

      // Save this fitness  for future comparison
      this->bestFitnessLeft = currentFitnessLeft;

      // Save this policy
      *this->bestPolicyLeft = *this->currentPolicy_;
      *this->bestInterpolationCacheLeft = *this->interpolationCache_;
    }

    // Compare with best left turn policy
    if (currentFitnessRight > this->bestFitnessRight){
      // Verbose
      std::cout << "Update best policy for right turn \n";

      // Save this fitness  for future comparison
      this->bestFitnessRight = currentFitnessRight;

      // Save this policy
      *this->bestPolicyRight = *this->currentPolicy_;
      *this->bestInterpolationCacheRight = *this->interpolationCache_;
    }

    //////////////////////////////////////////////////////////
    /// THE SEQUEL NEEDS TO BE PERFORMED FOR ALL THREE SUB-BRAINS
    ////////////////////////////////////////////////////////////
    // Insert ranked policy in list
    PolicyPtr backupPolicy = std::make_unique< Policy >(_numSplines);

    for (size_t i = 0; i < _numSplines; ++i)
    {
      auto &spline = this->currentPolicy_->at(i);
      backupPolicy->at(i) = Spline(spline.begin(), spline.end());

      spline.resize(this->sourceYSize_);
    }

    // Insert ranked policy in list
    this->rankedPoliciesGait.insert({currentFitnessGait, backupPolicy});
    this->rankedPoliciesLeft.insert({currentFitnessLeft, backupPolicy});
    this->rankedPoliciesRight.insert({currentFitnessRight, backupPolicy});

    // Remove worst policies
    while (this->rankedPoliciesGait.size() > this->maxRankedPolicies_){
      auto last = std::prev(this->rankedPoliciesGait.end());
      this->rankedPoliciesGait.erase(last);
    }

    while (this->rankedPoliciesLeft.size() > this->maxRankedPolicies_){
      auto last1 = std::prev(this->rankedPoliciesLeft.end());
      this->rankedPoliciesLeft.erase(last1);
    }

    while (this->rankedPoliciesRight.size() > this->maxRankedPolicies_){
      auto last2 = std::prev(this->rankedPoliciesRight.end());
      this->rankedPoliciesRight.erase(last2);
    }

    // Update generation counter and check is it finished
    if (this->generationCounter_ == this->maxEvaluations_)
    {
      std::exit(0);
    }

    // Increase spline points if it is a time
    if (this->generationCounter_ % this->stepRate_ == 0)
    {
      this->IncreaseSplinePoints(_numSplines);
    }

    /// Actual policy generation

    /// Determine which mutation operator to use
    /// Default, for algorithms A and B, is used standard normal distributionyp
    /// with decaying sigma. For algorithms C and D, is used normal distribution
    /// with self-adaptive sigma.
    std::random_device rd;
    std::mt19937 mt(rd());

    if (this->algorithmType_ == "C" or this->algorithmType_ == "D")
    {
      // uncorrelated mutation with one step size
      std::mt19937 sigma_mt(rd());
      std::normal_distribution< double > sigma_dist(0, 1);
      this->sigma_ = this->sigma_ * std::exp(this->tau_ * sigma_dist(sigma_mt));
    }
    else
    {
      // Note: Unreachable by construction under algorithm C/D
      // Default is decayig sigma
      if (this->rankedPoliciesGait.size() >= this->maxRankedPolicies_)
      {
        this->sigma_ *= SIGMA;
      }
    }
    std::normal_distribution< double > dist(0, this->sigma_);

    /// Determine which selection operator to use
    /// Default, for algorithms A and C, is used ten parent crossover
    /// For algorithms B and D, is used two parent crossover with binary
    /// tournament selection
    if (this->rankedPoliciesGait.size() < this->maxRankedPolicies_)
    {
      // Generate random policy if number of stored policies is less then
      // `maxRankedPolicies_`
      for (size_t i = 0; i < _numSplines; ++i)
      {
        for (size_t j = 0; j < this->sourceYSize_; ++j)
        {
          (*this->currentPolicy_)[i][j] = dist(mt);
        }
      }
    }
    else
    {
      // Generate new policy using weighted crossover operator
      auto totalFitness = 0.0;
      if (this->algorithmType_ == "B" or this->algorithmType_ == "D")
      {
        // k-selection tournament
        auto parent1 = this->BinarySelection();
        auto parent2 = parent1;
        while (parent2 == parent1)
        {
          parent2 = this->BinarySelection();
        }

        auto fitness1 = parent1->first;
        auto fitness2 = parent2->first;

        auto policy1 = parent1->second;
        auto policy2 = parent2->second;

        // TODO: Verify what should be total fitness in binary
        totalFitness = fitness1 + fitness2;

        // For each spline
        for (size_t i = 0; i < _numSplines; ++i)
        {
          // And for each control point
          for (size_t j = 0; j < this->sourceYSize_; ++j)
          {
            // Apply modifier
            auto splinePoint = 0.0;
            splinePoint += ((policy1->at(i)[j] - (*this->currentPolicy_)[i][j])) * (fitness1 / totalFitness);
            splinePoint += ((policy2->at(i)[j] - (*this->currentPolicy_)[i][j])) * (fitness2 / totalFitness);

            // Add a mutation + current
            // TODO: Verify do we use current in this case
            splinePoint += dist(mt) + (*this->currentPolicy_)[i][j];

            // Set a newly generated point as current
            (*this->currentPolicy_)[i][j] = splinePoint;
          }
        }
      }
      else
      {
        // Default is all parents selection
        // Calculate first total sum of fitnesses
        for (auto const &it : this->rankedPoliciesGait)
        {
          auto fitness = it.first;
          totalFitness += fitness;
        }

        // For each spline
        // TODO: Verify that this should is correct formula
        for (size_t i = 0; i < _numSplines; ++i)
        {
          // And for each control point
          for (size_t j = 0; j < this->sourceYSize_; ++j)
          {
            // Apply modifier
            auto splinePoint = 0.0;
            for (auto const &it : this->rankedPoliciesGait)
            {
              auto fitness = it.first;
              auto policy = it.second;

              splinePoint += ((policy->at(i)[j] - (*this->currentPolicy_)[i][j])) * (fitness / totalFitness);
            }

            // Add a mutation + current
            // TODO: Verify do we use 'current_policy_' in this case
            splinePoint += dist(mt) + (*this->currentPolicy_)[i][j];

            // Set a newly generated point as current
            (*this->currentPolicy_)[i][j] = splinePoint;
          }
        }
      }
    }
    // Cache update for all sub-brains
    this->InterpolateCubic(_numSplines, this->currentPolicy_.get(), this->interpolationCache_.get());
  }
    // Set best in case we are finished with learning
  else{
    // Select relevant policy
    if(this->moveOrientation == "left"){
      *this->currentPolicy_ = *this->bestPolicyLeft;
      *this->interpolationCache_ = *this->bestInterpolationCacheLeft;
    }
    else if(this->moveOrientation == "right"){
      *this->currentPolicy_ = *this->bestPolicyRight;
      *this->interpolationCache_ = *this->bestInterpolationCacheRight;
    }
    else if(this->moveOrientation == "gait"){
      *this->currentPolicy_ = *this->bestPolicyGait;
      *this->interpolationCache_ = *this->bestInterpolationCacheGait;
    }
    else{
      std::cout << "Incorrect moveOrientation given \n";
    }
  }
}

void RLPower::IncreaseSplinePoints(const size_t _numSplines)
{
  this->sourceYSize_++;

  // LOG code
  this->stepRate_ = this->numInterpolationPoints_ / this->sourceYSize_;

  // Copy current policy for resizing
  Policy policy_copy(this->currentPolicy_->size());
  for (size_t i = 0; i < _numSplines; ++i)
  {
    auto &spline = this->currentPolicy_->at(i);
    policy_copy[i] = Spline(spline.begin(), spline.end());

    spline.resize(this->sourceYSize_);
  }

  this->InterpolateCubic(0, &policy_copy, this->currentPolicy_.get());

  //////////////////////////////////////////////////////////////
  // Call desired policy out of {gait,left,right}
  auto tempPolicy = this->rankedPoliciesGait;

  if(this->moveOrientation == "left"){
    tempPolicy = this->rankedPoliciesLeft;
    std::cout << "WARNING: Spline points increased based on left controller \n";
  }
  else if(this->moveOrientation == "right"){
    tempPolicy = this->rankedPoliciesRight;
    std::cout << "WARNING: Spline points increased based on right controller \n";
  }
  else if(this->moveOrientation == "gait"){
    std::cout << "WARNING: Spline points increased based on gait controller \n";
  }
  else{
    std::cout << "WARNING: Spline points increased based on random controller \n";
  }

  for (auto &it : tempPolicy)
  {
    auto policy = it.second;

    for (size_t j = 0; j < _numSplines; ++j)
    {
      auto &spline = policy->at(j);
      policy_copy[j] = Spline(spline.begin(), spline.end());
      spline.resize(this->sourceYSize_);
    }
    this->InterpolateCubic(0, &policy_copy, policy.get());
  }

}

std::map< double, PolicyPtr >::iterator RLPower::BinarySelection()
{
  std::random_device rd;
  std::mt19937 umt(rd());
  std::uniform_int_distribution <size_t> udist(0, this->maxRankedPolicies_ - 1);

  // Select two different numbers from uniform distribution
  // U(0, max_ranked_policies_ - 1
  size_t pindex1, pindex2;
  pindex1 = udist(umt);
  do
  {
    pindex2 = udist(umt);
  } while (pindex1 == pindex2);

  // Set iterators to begin of the 'ranked_policies_' map
  auto individual1 = this->rankedPoliciesGait.begin();
  auto individual2 = this->rankedPoliciesGait.begin();

  // Get parents based on moving (learning if we're here) orientation
  if(this->moveOrientation == "left"){
    // Set iterators to begin of the 'ranked_policies_' map
    individual1 = this->rankedPoliciesLeft.begin();
    individual2 = this->rankedPoliciesLeft.begin();
  }
  else if(this->moveOrientation == "right"){
    individual1 = this->rankedPoliciesRight.begin();
    individual2 = this->rankedPoliciesRight.begin();
  }

  // Move iterators to indices positions
  std::advance(individual1, pindex1);
  std::advance(individual2, pindex2);

  auto fitness1 = individual1->first;
  auto fitness2 = individual2->first;

  return fitness1 > fitness2 ? individual1 : individual2;
}

// seconds
const double RLPower::CYCLE_LENGTH = 5;

// sigma decay
const double RLPower::SIGMA = 0.98;

double RLPower::Fitness(std::string controllerType)
{
  return this->evaluator_->Fitness(controllerType);
}

void RLPower::Modify(ConstModifyPolicyPtr &/* _request */)
{
  boost::mutex::scoped_lock lock(this->rlpowerMutex_);

  // TODO: Implement the rest of the method
}

void RLPower::Output(
    const size_t _numSplines,
    const double _time,
    double *_output)
{
  if (this->cycleStartTime_ < 0)
  {
    this->cycleStartTime_ = _time;
  }

  // get correct X value (between 0 and CYCLE_LENGTH)
  auto x = _time - this->cycleStartTime_;
  while (x >= RLPower::CYCLE_LENGTH)
  {
    this->cycleStartTime_ += RLPower::CYCLE_LENGTH;
    x = _time - this->cycleStartTime_;
  }

  // adjust X on the cache coordinate space
  x = (x / CYCLE_LENGTH) * this->numInterpolationPoints_;
  // generate previous and next values
  auto x_a = ((int)x) % this->numInterpolationPoints_;
  auto x_b = (x_a + 1) % this->numInterpolationPoints_;

  // linear interpolation for every actuator
  for (size_t i = 0; i < _numSplines; ++i)
  {
    auto y_a = this->interpolationCache_->at(i)[x_a];
    auto y_b = this->interpolationCache_->at(i)[x_b];

    _output[i] = y_a + ((y_b - y_a) * (x - x_a) / (x_b - x_a));
  }
}
