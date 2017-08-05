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

#include <iostream>
#include <string>
#include <stdexcept>

#include <revolve/gazebo/sensors/SensorFactory.h>
#include <revolve/gazebo/sensors/Sensors.h>

namespace gz = gazebo;

namespace revolve
{
  namespace gazebo
  {
    SensorFactory::SensorFactory(gz::physics::ModelPtr model)
            : model_(model)
    {}

    SensorFactory::~SensorFactory()
    {}

    SensorPtr SensorFactory::getSensor(sdf::ElementPtr sensor,
                                       const std::string &type,
                                       const std::string &partId,
                                       const std::string &sensorId)
    {
      SensorPtr out;
      if ("imu" == type)
      {
        out.reset(new ImuSensor(this->model_, sensor, partId, sensorId));
      }
      else if ("light" == type)
      {
        out.reset(new LightSensor(this->model_, sensor, partId, sensorId));
      }
      else if ("touch" == type)
      {
        out.reset(new TouchSensor(this->model_, sensor, partId, sensorId));
      }
      else if ("basic_battery" == type)
      {
        out.reset(new BatterySensor(this->model_, partId, sensorId));
      }
      else if ("point_intensity" == type)
      {
        out.reset(new PointIntensitySensor(sensor,
                                           this->model_,
                                           partId,
                                           sensorId));
      }

      return out;
    }

    SensorPtr SensorFactory::create(sdf::ElementPtr sensor)
    {
      auto typeParam = sensor->GetAttribute("type");
      auto partIdParam = sensor->GetAttribute("part_id");
      auto idParam = sensor->GetAttribute("id");

      if (not typeParam || not partIdParam || not idParam)
      {
        std::cerr << "Sensor is missing required attributes "
                "(`id`, `type` or `part_id`)." << std::endl;
        throw std::runtime_error("Sensor error");
      }

      auto partId = partIdParam->GetAsString();
      auto type = typeParam->GetAsString();
      auto id = idParam->GetAsString();

      SensorPtr out = this->getSensor(sensor, type, partId, id);
      if (not out)
      {
        std::cerr
                << "Sensor type '"
                << type
                << "' is not supported."
                << std::endl;
        throw std::runtime_error("Sensor error");
      }

      return out;
    }
  }  /* namespace gazebo */
}  /* namespace tol_robogen */
