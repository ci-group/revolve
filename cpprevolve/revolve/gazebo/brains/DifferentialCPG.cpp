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
    const sdf::ElementPtr _settings,
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

  std::cout << _settings->GetDescription() << std::endl;
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
    auto coordX = motor->GetAttribute("x")->GetAsString();
    auto coordY = motor->GetAttribute("y")->GetAsString();
//    TODO: Add this check
//    if (this->layerMap_.count({x, y}))
//    {
//      std::cerr << "Duplicate motor ID '" << x << "," << y << "'" <<
//      std::endl;
//      throw std::runtime_error("Robot brain error");
//    }

//    this->bias_[{coordX, coordY}] = 0;
//    this->gain_[std::make_tuple(coordX, coordY)] = 0;

//    auto AtoB =
//    this->connections_[std::make_tuple(coordX, coordY, 1, coordX, coordY, -1);] = 1;
//    auto BtoA = ;
//    this->connections_[std::make_tuple(coordX, coordY, -1, coordX, coordY, 1)] = 1;

    motorsMap[motorId] = motor;
    toProcess.insert(motorId);

    motor = motor->GetNextElement("rv:motor");
  }


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

  // TODO Update diffCPG
  auto *output = new double[numMotors];
//  this->Output(numMotors, _time, output);

  // Send new signals to the motors
  p = 0;
  for (const auto &motor: _motors)
  {
    motor->Update(&output[p], _step);
    p += motor->Outputs();
  }
}
