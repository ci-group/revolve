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
 * Date: 10-09-18
 *
 */

#include <cmath>

#include "Evaluator.h"

using namespace revolve::gazebo;

/////////////////////////////////////////////////
Evaluator::Evaluator(const double _evaluationRate)
{
  assert(_evaluationRate > 0 and "`_evaluationRate` should be greater than 0");
  this->evaluationRate_ = _evaluationRate;
  this->counter = 0;
  this->bestFitnessGait = 0;
  this->bestFitnessLeft = 0;
  this->bestFitnessRight = 0;
  this->currentPosition_.Reset();
  this->previousPosition_.Reset();
}

/////////////////////////////////////////////////
Evaluator::~Evaluator() = default;

/////////////////////////////////////////////////
void Evaluator::Reset()
{
  this->previousPosition_ = this->currentPosition_;
  this->counter++;
}

/////////////////////////////////////////////////
double Evaluator::Fitness()
{
  // Verbose
  std::cout << "Iteration: " << this->counter << "\n";

  // Argument
  std::string controllerType = "leftTurn";

  // Parameter penalty for moving (for the steering controllers)
  double p = 0.0;

  // Working variable
  double dS = 0;
  double gait = std::sqrt(std::pow(this->previousPosition_.Pos().X() -
                                   this->currentPosition_.Pos().X(), 2) +
                          std::pow(this->previousPosition_.Pos().Y() -
                                   this->currentPosition_.Pos().Y(), 2));

  std::cout << "Gait is " << gait/this->evaluationRate_ << std::endl;
  if (controllerType == "gait"){
    return (gait/this->evaluationRate_);
  }

  // Get angles in degrees in case of left/right turn controller
  auto c = 180.0/3.14159;
  auto x1 =this->previousPosition_.Rot().X()*c;
  auto y1 =this->previousPosition_.Rot().Y()*c;
  auto z1 =this->previousPosition_.Rot().Z()*c;
  auto x2 =this->currentPosition_.Rot().X()*c;
  auto y2 =this->currentPosition_.Rot().Y()*c;
  auto z2 =this->currentPosition_.Rot().Z()*c;

  std::cout << "Previous angles: " << x1 << ", " << y1 << ", " << z1
            <<std::endl;
  std::cout << "Current angles: " << x2 << ", " << y2 << ", " << z2 <<
            std::endl;
  std::cout << "Scaled angle difference: "
  << (z2 - z1)/this->evaluationRate_ << "\n \n";

  //TODO: Deal with 2*PI boundary
  if (controllerType == "leftTurn"){
    // UPDATE LINE TEMPORARY ONLY!!!!!
    this->previousPosition_ = this->currentPosition_;
    this->counter++;
    double fitness = (z2 - z1 - p*gait)/this->evaluationRate_;
    if (fitness > this->bestFitnessLeft){
      this->bestFitnessLeft = fitness;
    }
    std::cout << "Best left fitness is " << this->bestFitnessLeft << std::endl;
    // UPPER LINE TEMPORARY ONLY!!!!!
    return (z2 - z1 - p*gait)/this->evaluationRate_;
  }
  else if (controllerType == "rightTurn"){
    // UPDATE LINE TEMPORARY ONLY!!!!!
    this->previousPosition_ = this->currentPosition_;
    this->counter++;
    double fitness = (z1 - z2 - p*gait)/this->evaluationRate_;
    if (fitness > this->bestFitnessRight){
      this->bestFitnessLeft = fitness;
    }
    std::cout << "Best right fitness is " << this->bestFitnessRight <<
    std::endl;
    // UPPER LINE TEMPORARY ONLY!!!!!

    return (z1 - z2 - p*gait)/this->evaluationRate_;
  }
  else{
    std::cout << "No valid controller specified \n";
  }

  // Update position: This need to be done manually with reset after the
  // fitness function is called using the reset function
  // this->previousPosition_ = this->currentPosition_;
}

/////////////////////////////////////////////////
void Evaluator::Update(const ignition::math::Pose3d &_pose)
{
  this->currentPosition_ = _pose;
}
