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

#include "PointIntensitySensor.h"

namespace gz = gazebo;

namespace revolve {
namespace gazebo {

PointIntensitySensor::PointIntensitySensor(sdf::ElementPtr sensor, ::gazebo::physics::ModelPtr model,
                       std::string partId, std::string sensorId):
    VirtualSensor(model, partId, sensorId, 1),
    i_max_(1),
    r_(1)
{

  if (not sensor->HasElement("rv:point_intensity_sensor")) {
    std::cerr << "PointIntensitySensor missing `rv:point_intensity_sensor` element." << std::endl;
    throw std::runtime_error("Robot brain error.");
  }

  auto configElem = sensor->GetElement("rv:point_intensity_sensor");

  if (not configElem->HasElement("rv:point")) {
    std::cerr << "PointIntensitySensor missing `rv:point` element." << std::endl;
  }

  auto pointElem = configElem->GetElement("rv:point");
  this->point_ = pointElem->Get< gz::math::Vector3 >();

  if (configElem->HasElement("rv:function")) {
    auto funcElem = configElem->GetElement("rv:function");

    if (funcElem->HasAttribute("r")) {
      funcElem->GetAttribute("r")->Get(this->r_);
    }

    if (funcElem->HasAttribute("i_max")) {
      funcElem->GetAttribute("i_max")->Get(this->i_max_);
    }
  }
}

///////////////////////////////////

void PointIntensitySensor::read(double * input) {
  double distance = this->model_->GetWorldPose().pos.Distance(this->point_);

  if (distance < this->r_) {
    input[0] = this->i_max_;
  } else {
    input[0] = this->i_max_ * pow(this->r_ / distance, 2);
  }
}

}
}
