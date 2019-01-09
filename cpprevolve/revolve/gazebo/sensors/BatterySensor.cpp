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

using namespace revolve::gazebo;

/////////////////////////////////////////////////
BatterySensor::BatterySensor(
    ::gazebo::physics::ModelPtr _model,
    std::string _partId,
    std::string _sensorId)
    : VirtualSensor(_model, _partId, _sensorId, 1)
{
  // Find the revolve plugin to get the battery data
  auto modelSdf = _model->GetSDF();
  if (modelSdf->HasElement("plugin"))
  {
    auto pluginSdf = modelSdf->GetElement("plugin");
    while (pluginSdf)
    {
      if (pluginSdf->HasElement("rv:robot_config"))
      {
        // Found revolve plugin
        auto settingsSdf = pluginSdf->GetElement("rv:robot_config");
        if (settingsSdf->HasElement("rv:battery"))
        {
          this->battery_ = settingsSdf->GetElement("rv:battery");
        }

        break;
      }
      pluginSdf = pluginSdf->GetNextElement("plugin");
    }
  }
}

/////////////////////////////////////////////////
void BatterySensor::Read(double *_input)
{
  _input[0] = this->battery_ and
             (this->battery_->HasElement("rv:level") ?
             this->battery_->GetElement("rv:level")->Get< double >() : 0.0);
}
