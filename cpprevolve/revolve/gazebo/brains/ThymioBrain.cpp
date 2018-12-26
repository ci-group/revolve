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
 * Date: 28/10/2018
 *
 */

#include <random>
#include <vector>

#include "ThymioBrain.h"
#include "../motors/Motor.h"
#include "../sensors/Sensor.h"

namespace gz = gazebo;

using namespace revolve::gazebo;

ThymioBrain::ThymioBrain(
    ::gazebo::physics::ModelPtr _model,
    sdf::ElementPtr /* _node */,
    std::vector< MotorPtr > &/* _motors */,
    std::vector< SensorPtr > &/* _sensors */)
{
  std::cout << "Hello!" << std::endl;
  this->robot_ = _model;
  std::cout << this->robot_->GetName() << std::endl;
}

ThymioBrain::~ThymioBrain() = default;

void ThymioBrain::Update(
    const std::vector< MotorPtr > &_motors,
    const std::vector< SensorPtr > &/* _sensors */,
    double /* _time */,
    double _step)
{
  std::random_device rd;
  std::mt19937 mt(rd());
  std::normal_distribution< double > dist(0, 1);

  auto numMotors = _motors.size();
  auto *output = new double[numMotors];
  for (size_t i = 0; i < numMotors; ++i)
  {
    output[i] += std::abs(dist(mt));
  }

  std::cout << "Output: " << output[0] << std::endl;

  // Send new signals to the actuators
  auto p = 0;
  for (const auto &motor: _motors)
  {
    motor->Update(&output[p], _step);
    p += motor->Outputs();
  }
}
