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
#include <random>
#include "Evaluator.h"

using namespace revolve::gazebo;

/////////////////////////////////////////////////
Evaluator::Evaluator(const double _evaluationRate)
{
  assert(_evaluationRate > 0 and "`_evaluationRate` should be greater than 0");
  this->evaluationRate_ = _evaluationRate;
  this->iteration = 0;
  this->penalty = 7.0;  // Parameter penalty for moving (for the steering controllers), e.g. 10
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
  this->iteration++;
}
/////////////////////////////////////////////////
double Evaluator::Fitness(std::string controllerType)
{
  // Working variable
  double gait = std::sqrt(std::pow(this->previousPosition_.Pos().X() -
                                   this->currentPosition_.Pos().X(), 2) +
                          std::pow(this->previousPosition_.Pos().Y() -
                                   this->currentPosition_.Pos().Y(), 2));


  // Get angles in degrees for left/right turn controller
  auto c = 180.0/3.14159;
  auto z1 = this->previousPosition_.Rot().Z()*c;
  auto z2 = this->currentPosition_.Rot().Z()*c;

  // Verbose
  std::cout << "\nIteration: " << this->iteration << "\n";
  std::cout << "Previous position: " << this->previousPosition_.Pos().X() << ", " << this->previousPosition_.Pos().Y() << std::endl;
  std::cout << "Current position " << this->currentPosition_.Pos().X() << ", "<< this->currentPosition_.Pos().Y() << std::endl;
  //std::cout << "Previous z-angle: " << z1 << std::endl;
  //std::cout << "Current z-angle: " << z2 << std::endl;

  // Enter controllers
  if (controllerType == "gait"){
    // Obtain fitness, as defined in https://doi.org/10.1162/ARTL_a_00223
    double fitness = std::pow(100.0*gait/this->evaluationRate_,6);

    // Update best fitness
    if (fitness > this->bestFitnessGait){
      this->bestFitnessGait = fitness;
    }

    // Verbose
    std::cout << "Gait: Fitness: " <<  fitness  << ". Best: " << this->bestFitnessGait << std::endl;

    return (fitness);
  }
  //TODO: Deal with 2*PI boundary
  else if (controllerType == "left"){
    // Obtain fitness
    double fitness = (z2 - z1 - this->penalty*gait)/this->evaluationRate_;

    // Update best fitness
    if (fitness > this->bestFitnessLeft){
      this->bestFitnessLeft = fitness;
    }

    // Verbose
    std::cout << "Left: Fitness: " << fitness << ". Best: " << this->bestFitnessLeft << std::endl;

    return fitness;
  }
  else if (controllerType == "right"){
    // Obtain fitness
    double fitness = (z1 - z2 - this->penalty*gait)/this->evaluationRate_;

    // Update best fitness
    if (fitness > this->bestFitnessRight){
      this->bestFitnessRight = fitness;
    }

    // Verbose
    std::cout << "Right: Fitness: " << fitness << ". Best: " <<this->bestFitnessRight << std::endl;

    return fitness;
  }
  else{
    std::cout << "No valid controller specified \n";
  }
}

/////////////////////////////////////////////////
void Evaluator::Update(const ignition::math::Pose3d &_pose)
{
  this->currentPosition_ = _pose;
}
