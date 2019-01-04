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

#include "DifferentialCPG.h"
#include "../motors/Motor.h"
#include "../sensors/Sensor.h"
#include "../util/YamlBodyParser.h"

namespace gz = gazebo;

using namespace revolve::gazebo;

/////////////////////////////////////////////////
DifferentialCPG::DifferentialCPG(
    const ::gazebo::physics::ModelPtr &_model,
    const sdf::ElementPtr &_node,
    const std::vector< revolve::gazebo::MotorPtr > &_motors,
    const std::vector< revolve::gazebo::SensorPtr > &_sensors)
    : flipState_(false)
{
  // Create transport node
  this->node_.reset(new gz::transport::Node());
  this->node_->Init();

  auto name = _model->GetName();
  // Listen to network modification requests
//  alterSub_ = node_->Subscribe(
//      "~/" + name + "/modify_diff_cpg", &DifferentialCPG::Modify,
//      this);

  auto numMotors = _motors.size();
  auto numSensors = _sensors.size();

  auto genome = _node->GetAttribute("genome")->GetAsString();
  auto parser = new YamlBodyParser(genome);


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
}
