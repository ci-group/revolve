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

#include "PointIntensitySensor.h"

namespace gz = gazebo;

using namespace revolve::gazebo;

/////////////////////////////////////////////////
PointIntensitySensor::PointIntensitySensor(
    sdf::ElementPtr _sensor,
    ::gazebo::physics::ModelPtr _model,
    std::string _partId,
    std::string _sensorId)
    : VirtualSensor(_model, _partId, _sensorId, 1)
    , maxInput_(1)
    , r_(1)
{
  if (not _sensor->HasElement("rv:point_intensity_sensor"))
  {
    std::cerr << "PointIntensitySensor missing "
        "`rv:point_intensity_sensor` element." << std::endl;
    throw std::runtime_error("Robot brain error.");
  }

  auto configElem = _sensor->GetElement("rv:point_intensity_sensor");

  if (not configElem->HasElement("rv:point"))
  {
    std::cerr << "PointIntensitySensor missing `rv:point` element."
              << std::endl;
  }

  auto pointElem = configElem->GetElement("rv:point");
  this->point_ = pointElem->Get< ignition::math::Vector3d >();

  if (configElem->HasElement("rv:function"))
  {
    auto funcElem = configElem->GetElement("rv:function");

    if (funcElem->HasAttribute("r"))
    {
      funcElem->GetAttribute("r")->Get(this->r_);
    }

    if (funcElem->HasAttribute("i_max"))
    {
      funcElem->GetAttribute("i_max")->Get(this->maxInput_);
    }
  }
}

/////////////////////////////////////////////////
void PointIntensitySensor::Read(double *_input)
{
  auto distance = this->model_->WorldPose().Pos().Distance(this->point_);

  if (distance < this->r_)
  {
    _input[0] = this->maxInput_;
  }
  else
  {
    _input[0] = this->maxInput_ * std::pow(this->r_ / distance, 2);
  }
}
