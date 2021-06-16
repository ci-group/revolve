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

#include <string>

#include <revolve/gazebo/sensors/Sensor.h>
#include <gazebo/physics/Model.hh>
#include <gazebo/sensors/sensors.hh>

namespace gz = gazebo;

using namespace revolve::gazebo;

/////////////////////////////////////////////////
Sensor::Sensor(
    ::gazebo::physics::ModelPtr _model,
    sdf::ElementPtr _sensor,
    std::string _partId,
    std::string _sensorId,
    unsigned int _inputs)
    : ::revolve::Sensor(_inputs)
    , partId_(_partId)
    , sensorId_(_sensorId)
    , sensor_(nullptr)
{
  if (not _sensor->HasAttribute("sensor") or not _sensor->HasAttribute("link"))
  {
    std::cerr << "Sensor is missing required attributes (`link` or `sensor`)."
              << std::endl;
    throw std::runtime_error("Sensor error");
  }

  auto sensorName = _sensor->GetAttribute("sensor")->GetAsString();
  auto linkName = _sensor->GetAttribute("link")->GetAsString();

  auto link = _model->GetLink(linkName);
  if (not link)
  {
    std::cerr << "Link '" << linkName << "' for sensor '" << sensorName
              << "' is not present in model." << std::endl;
    throw std::runtime_error("Sensor error");
  }

  std::string scopedName = link->GetScopedName(true) + "::" + sensorName;
  this->sensor_ = gz::sensors::get_sensor(scopedName);

  if (not this->sensor_)
  {
    std::cerr << "Sensor with scoped name '" << scopedName
              << "' could not be found." << std::endl;
    throw std::runtime_error("Sensor error");
  }
}
