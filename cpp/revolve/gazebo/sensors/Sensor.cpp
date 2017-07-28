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

#include <revolve/gazebo/sensors/Sensor.h>

namespace gz = gazebo;

namespace revolve {
namespace gazebo {

Sensor::Sensor(::gazebo::physics::ModelPtr model, sdf::ElementPtr sensor,
    std::string partId, std::string sensorId, unsigned int inputs):
  VirtualSensor(model, partId, sensorId, inputs)
{
  if (!sensor->HasAttribute("sensor") || !sensor->HasAttribute("link")) {
    std::cerr << "Sensor is missing required attributes (`link` or `sensor`)." << std::endl;
    throw std::runtime_error("Sensor error");
  }

  auto sensorName = sensor->GetAttribute("sensor")->GetAsString();
  auto linkName = sensor->GetAttribute("link")->GetAsString();

  auto link = model->GetLink(linkName);
  if (!link) {
    std::cerr << "Link '" << linkName << "' for sensor '"
        << sensorName << "' is not present in model." << std::endl;
    throw std::runtime_error("Sensor error");
  }

  std::string scopedName = link->GetScopedName(true) + "::" + sensorName;
  this->sensor_ = gz::sensors::get_sensor(scopedName);

  if (!this->sensor_) {
    std::cerr << "Sensor with scoped name '" << scopedName
        << "' could not be found." << std::endl;
    throw std::runtime_error("Sensor error");
  }
}

Sensor::~Sensor()
{}

::gazebo::sensors::SensorPtr Sensor::gzSensor() {
  return sensor_;
}

} /* namespace gazebo */
} /* namespace tol_robogen */
