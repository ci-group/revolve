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
    sdf::ElementPtr _sensor,
    const std::string &_type,
    const std::string &_partId,
    const std::string &_sensorId)
{
  SensorPtr out;
  if ("imu" == _type)
  {
    out.reset(new ImuSensor(this->model_, _sensor, _partId, _sensorId));
  }
  else if ("light" == _type)
  {
    out.reset(new LightSensor(this->model_, _sensor, _partId, _sensorId));
  }
  else if ("touch" == _type)
  {
    out.reset(new TouchSensor(this->model_, _sensor, _partId, _sensorId));
  }
  else if ("basic_battery" == _type)
  {
    out.reset(new BatterySensor(this->model_, _partId, _sensorId));
  }
  else if ("point_intensity" == _type)
  {
    out.reset(new PointIntensitySensor(_sensor,
                                       this->model_,
                                       _partId,
                                       _sensorId));
  }

  return out;
}

/////////////////////////////////////////////////
SensorPtr SensorFactory::Create(sdf::ElementPtr _sensor)
{
  auto typeParam = _sensor->GetAttribute("type");
  auto partIdParam = _sensor->GetAttribute("part_id");
  auto idParam = _sensor->GetAttribute("id");

  if (not typeParam or not partIdParam or not idParam)
  {
    std::cerr << "Sensor is missing required attributes (`id`, `type` or "
        "`part_id`)." << std::endl;
    throw std::runtime_error("Sensor error");
  }

  auto partId = partIdParam->GetAsString();
  auto type = typeParam->GetAsString();
  auto id = idParam->GetAsString();

  SensorPtr out = this->Sensor(_sensor, type, partId, id);
  if (not out)
  {
    std::cerr << "Sensor type '" << type << "' is not supported." << std::endl;
    throw std::runtime_error("Sensor error");
  }

  return out;
}
