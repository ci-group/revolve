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
*
*/

#include <string>

#include "BatterySensor.h"

namespace gz = gazebo;

namespace revolve
{
  namespace gazebo
  {
    BatterySensor::BatterySensor(
            ::gazebo::physics::ModelPtr model,
            std::string partId,
            std::string sensorId)
            : VirtualSensor(model, partId, sensorId, 1)
    {
      // Find the revolve plugin to get the battery data
      auto modelSdf = model->GetSDF();
      if (modelSdf->HasElement("plugin"))
      {
        auto pluginElem = modelSdf->GetElement("plugin");
        while (pluginElem)
        {
          if (pluginElem->HasElement("rv:robot_config"))
          {
            // Found revolve plugin
            auto settings = pluginElem->GetElement("rv:robot_config");
            if (settings->HasElement("rv:battery"))
            {
              this->batteryElem = settings->GetElement("rv:battery");
            }

            break;
          }
          pluginElem = pluginElem->GetNextElement("plugin");
        }
      }
    }

///////////////////////////////////

    void BatterySensor::read(double *input)
    {
      input[0] =
              this->batteryElem && this->batteryElem->HasElement("rv:level") ?
              this->batteryElem->GetElement("rv:level")->Get< double >() : 0.0;
    }
  }
}
