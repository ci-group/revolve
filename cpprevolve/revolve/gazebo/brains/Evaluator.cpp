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

double measureDistance(
    const ignition::math::Pose3d &_pose1,
    const ignition::math::Pose3d &_pose2)
{
  std::cout << "_pose: " << _pose1.Pos().X() << " " << _pose1.Pos().Y() << " "
            << _pose2.Pos().X() << " " << _pose2.Pos().Y() << std::endl;
  return std::sqrt(std::pow(_pose1.Pos().X() - _pose2.Pos().X(), 2) +
                   std::pow(_pose1.Pos().Y() - _pose2.Pos().Y(), 2));
}

/////////////////////////////////////////////////
Evaluator::Evaluator(const double _evaluationRate)
{
  assert(_evaluationRate > 0 and "`_evaluationRate` should be greater than 0");
  this->evaluationRate_ = _evaluationRate;

  this->currentPosition_.Reset();
  this->previousPosition_.Reset();
  this->startPosition_.Reset();
  this->pathLength = 0;
}

/////////////////////////////////////////////////
Evaluator::~Evaluator() = default;

/////////////////////////////////////////////////
void Evaluator::Reset(double time)
{
  this->pathLength = 0;
  this->startPosition_ = this->currentPosition_;
}

/////////////////////////////////////////////////
double Evaluator::Fitness()
{
  /*
    auto dS = this->currentPosition_.Pos().X() - this->startPosition_.Pos().X();
    */

  double dS = measureDistance(this->startPosition_, this->currentPosition_);

  return dS / this->evaluationRate_;

}

/////////////////////////////////////////////////
void Evaluator::Update(const ignition::math::Pose3d &_pose,
                       const double time,
                       const double step)
{
  this->pathLength += measureDistance(currentPosition_, _pose);
  this->previousPosition_ = currentPosition_;
  this->currentPosition_ = _pose;
}
