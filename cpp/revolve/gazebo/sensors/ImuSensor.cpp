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
* Author: Elte Hupkes
* Date: Mar 24, 2015
*
*/

#include <cstring>
#include <string>

#include "ImuSensor.h"

namespace gz = gazebo;

using namespace revolve::gazebo;

/////////////////////////////////////////////////
ImuSensor::ImuSensor(
    ::gazebo::physics::ModelPtr _model,
    sdf::ElementPtr _sensor,
    std::string _partId,
    std::string _sensorId)
    : Sensor(_model, _sensor, _partId, _sensorId, 6)
{
  this->castSensor_ =
      boost::dynamic_pointer_cast< gz::sensors::ImuSensor >(this->sensor_);

  if (not this->castSensor_)
  {
    std::cerr << "Creating an IMU sensor with a non-IMU sensor object."
              << std::endl;
    throw std::runtime_error("Sensor error");
  }

  // Initialize all initial values to zero
  std::memset(this->lastValues_, 0, sizeof(this->lastValues_));

  // Add update connection that will produce new value
  this->updateConnection_ = this->castSensor_->ConnectUpdated(
      boost::bind(&ImuSensor::OnUpdate, this));
}

/////////////////////////////////////////////////
ImuSensor::~ImuSensor() = default;

/////////////////////////////////////////////////
void ImuSensor::OnUpdate()
{
  // Store the recorded values
  auto acc = this->castSensor_->LinearAcceleration();
  auto velo = this->castSensor_->AngularVelocity();
  this->lastValues_[0] = acc[0];
  this->lastValues_[1] = acc[1];
  this->lastValues_[2] = acc[2];
  this->lastValues_[3] = velo[0];
  this->lastValues_[4] = velo[1];
  this->lastValues_[5] = velo[2];
}

/////////////////////////////////////////////////
void ImuSensor::Read(double *_input)
{
  // Copy our values to the input array
  memcpy(_input, this->lastValues_, sizeof(this->lastValues_));
}
