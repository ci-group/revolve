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
  this->previousAngle = 0;
  this->evaluationRate_ = _evaluationRate;
  this->iteration = 0;
  this->penaltyTurn = 0.05;
  this->penaltyGait = 1.0; // 1.0: linear; tbd. Ex: 0.03 travelled with 8 degrees. Maybe 100?
  this->gaitThreshold = 0.0004; // Tbd. Now done empirically
  this->turnThreshold = 1.5; // In degrees
  this->bestFitnessGait = -100.f;
  this->bestFitnessLeft = -100.f;
  this->bestFitnessRight = -100.f;
  this->currentPosition_.Reset();
  this->previousPosition_.Reset();
  this->printOutput = true;
  this->moveDirectional = false;

  // Create fitness directory
  this->filename = "output/rlpower/";
  this->filename += std::to_string(time(0)) + "/";
  std::system(("mkdir -p " + this->filename).c_str());
}


/////////////////////////////////////////////////
Evaluator::~Evaluator() = default;

/////////////////////////////////////////////////
void Evaluator::Reset()
{
  this->previousPosition_ = this->currentPosition_;
  this->previousAngle = this->currentPosition_.Rot().Yaw()*180.0/M_PI;
  this->iteration++;
  this->printOutput = true;

  // Write results to fitness file in format g,l,r
  std::ofstream fitnessFile;
  fitnessFile.open(this->filename + "fitness.txt", std::ios::app);
  fitnessFile << this->bestFitnessGait << ",";
  fitnessFile << this->bestFitnessLeft << ",";
  fitnessFile << this->bestFitnessRight << "\n";
  fitnessFile.close();
}

/////////////////////////////////////////////////
double Evaluator::Fitness(std::string controllerType)
{
  // Working variable
  double gait = std::sqrt(std::pow(this->previousPosition_.Pos().X() -
                                   this->currentPosition_.Pos().X(), 2) +
                          std::pow(this->previousPosition_.Pos().Y() -
                                   this->currentPosition_.Pos().Y(), 2))/this->evaluationRate_;

  // Get Z-angle in degrees
  double zAngleFromOrigin = this->currentPosition_.Rot().Yaw()*180.0/M_PI;
  double currentAngle = zAngleFromOrigin - this->previousAngle;

  // If we cross the boundary point from positive to negative
  if(this->previousAngle > 90 and zAngleFromOrigin < -90){
    currentAngle = 180 - this->previousAngle + 180 + zAngleFromOrigin;
    std::cout << "Crossed boundary from negative to positive \n";
  }
    // If we cross the boundary point from negative to positive
  else if(this->previousAngle < -90 and zAngleFromOrigin >90){
    currentAngle =-(180 + this->previousAngle + 180 - zAngleFromOrigin);
    std::cout << "Crossed boundary from positive to negative \n";
  }

  // Verbose
  if(this->printOutput){
    std::cout << "\nPrevious position: " << this->previousPosition_.Pos().X() << ", " << this->previousPosition_.Pos().Y() << std::endl;
    std::cout << "Current position " << this->currentPosition_.Pos().X() << ", "<< this->currentPosition_.Pos().Y() << std::endl;
    std::cout << "Previous z-angle: " << this->previousAngle << std::endl;
    std::cout << "Current z-angle: " << zAngleFromOrigin << std::endl;
    std::cout << "Degrees travelled: " << currentAngle << "\n";
    std::cout << "Relative distance travelled is: " << gait << "\n\n";
    this->printOutput = false;
  }

  // Enter controllers
  if (controllerType == "gait"){
    if (!this->moveDirectional){
      double fitness = 0;

      // Fitness higher than 0 if we are within our hard constraint
      if (abs(currentAngle) < this->turnThreshold)
      {
        double penalty = 0;
        fitness = gait - penalty;
      }

      // Update best fitness
      if (fitness > this->bestFitnessGait)
      {
        this->bestFitnessGait = fitness;
      }

      // Verbose
      std::cout << "Gait: Fitness: " << fitness << ". Best: " << this->bestFitnessGait << std::endl;

      return (fitness);
    }
    else
    {
      double fitness = 0;

      // Fitness higher than 0 if we are within our hard constraint
      if (abs(currentAngle) < this->turnThreshold)
      {
        double directed = (this->previousPosition_.Pos().X() - this->currentPosition_.Pos().X()) / this->evaluationRate_;
        double penalty = 0;
        fitness = directed - penalty;
      }

      // Update best fitness
      if (fitness > this->bestFitnessGait)
      {
        this->bestFitnessGait = fitness;
      }

      // Verbose
      std::cout << "Directed: Fitness: " << fitness << ". Best: " << this->bestFitnessGait << std::endl;

      // Return scaled directed
      return fitness;
    }
  }
  else if (controllerType == "left"){
    double fitness = 0;

    // Fitness higher than 0 if we are within our hard constraint
    if (gait < this->gaitThreshold){
      double penalty = penaltyGait*gait/this->gaitThreshold;
      fitness = (currentAngle - penalty)/this->evaluationRate_;
    }

    // Update best fitness
    if (fitness > this->bestFitnessLeft){
      this->bestFitnessLeft = fitness;
    }

    // Verbose
    std::cout << "Left: Fitness: " << fitness << ". Best: " << this->bestFitnessLeft << std::endl;

    return fitness;
  }
  else if (controllerType == "right"){
    double fitness = 0;

    // Fitness higher than 0 if we are within our hard constraint
    if (gait < this->gaitThreshold){
      double penalty = penaltyGait*gait/this->gaitThreshold;
      fitness = (-currentAngle - penalty)/this->evaluationRate_;
    }

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
