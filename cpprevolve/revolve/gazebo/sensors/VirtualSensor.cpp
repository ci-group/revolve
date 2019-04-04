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
* Author: Elte Hupkes
*
*/

#include <string>

#include <revolve/gazebo/sensors/VirtualSensor.h>

using namespace revolve::gazebo;

/////////////////////////////////////////////////
VirtualSensor::VirtualSensor(
    ::gazebo::physics::ModelPtr _model,
    const std::string _partId,
    const std::string _sensorId,
    const unsigned int _inputs)
    : model_(_model)
    , partId_(_partId)
    , sensorId_(_sensorId)
    , inputs_(_inputs)
{
}

/////////////////////////////////////////////////
VirtualSensor::~VirtualSensor() = default;

/////////////////////////////////////////////////
unsigned int VirtualSensor::Inputs()
{
  return this->inputs_;
}

/////////////////////////////////////////////////
std::string VirtualSensor::PartId()
{
  return this->partId_;
}

/////////////////////////////////////////////////
std::string VirtualSensor::SensorId()
{
  return this->sensorId_;
}
