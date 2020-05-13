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

#include <revolve/gazebo/sensors/SensorFactory.h>
#include <revolve/gazebo/sensors/Sensors.h>

namespace gz = gazebo;

using namespace revolve::gazebo;

/////////////////////////////////////////////////
SensorFactory::SensorFactory(gz::physics::ModelPtr _model)
    : model_(_model)
{
}

/////////////////////////////////////////////////
SensorFactory::~SensorFactory() = default;

/////////////////////////////////////////////////
SensorPtr SensorFactory::Sensor(
    sdf::ElementPtr _sensorSdf,
    const std::string &_type,
    const std::string &_partId,
    const std::string &_sensorId)
{
  SensorPtr sensor;
  if ("imu" == _type)
  {
    sensor.reset(new ImuSensor(this->model_, _sensorSdf, _partId, _sensorId));
  }
  else if ("light" == _type)
  {
    sensor.reset(new LightSensor(this->model_, _sensorSdf, _partId, _sensorId));
  }
  else if ("contact" == _type) // touch sensor
  {
    sensor.reset(new TouchSensor(this->model_, _sensorSdf, _partId, _sensorId));
  }
  else
  {
      std::clog << "Sensor type \"" << _type << "\" not recognized. Ignoring sensor" << std::endl;
  }

  return sensor;
}

/////////////////////////////////////////////////
SensorPtr SensorFactory::Create(sdf::ElementPtr _sensorSdf)
{
  auto typeParam = _sensorSdf->GetAttribute("type");
  auto partIdParam = _sensorSdf->GetAttribute("part_id");
  auto idParam = _sensorSdf->GetAttribute("id");

  if (not typeParam or not partIdParam or not idParam)
  {
    std::cerr << "Sensor is missing required attributes (`id`, `type` or "
        "`part_id`)." << std::endl;
    throw std::runtime_error("Sensor error");
  }

  auto partId = partIdParam->GetAsString();
  auto type = typeParam->GetAsString();
  auto id = idParam->GetAsString();

  SensorPtr sensor = this->Sensor(_sensorSdf, type, partId, id);
  if (not sensor)
  {
    std::cerr << "Sensor type '" << type << "' is not supported." << std::endl;
    throw std::runtime_error("Sensor error");
  }

  return sensor;
}
