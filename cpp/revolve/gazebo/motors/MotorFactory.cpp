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
* Date: Mar 16, 2015
*
*/

#include <string>

#include <revolve/gazebo/motors/MotorFactory.h>
#include <revolve/gazebo/motors/Motors.h>

namespace gz = gazebo;

using namespace revolve::gazebo;

/////////////////////////////////////////////////
MotorFactory::MotorFactory(::gazebo::physics::ModelPtr _model)
    : model_(_model)
{
}

/////////////////////////////////////////////////
MotorFactory::~MotorFactory() = default;

/////////////////////////////////////////////////
MotorPtr MotorFactory::Motor(
    sdf::ElementPtr _motorSdf,
    const std::string &_type,
    const std::string &_motorId,
    const std::string &_partId)
{
  MotorPtr motor;
  if ("position" == _type)
  {
    motor.reset(new PositionMotor(model_, _motorId, _partId, _motorSdf));
  }
  else if ("velocity" == _type)
  {
    motor.reset(new VelocityMotor(model_, _motorId, _partId, _motorSdf));
  }

  return motor;
}

/////////////////////////////////////////////////
MotorPtr MotorFactory::Create(sdf::ElementPtr _motorSdf)
{
  auto typeParam = _motorSdf->GetAttribute("type");
  auto partIdParam = _motorSdf->GetAttribute("part_id");
  auto idParam = _motorSdf->GetAttribute("id");

  if (not typeParam or not partIdParam or not idParam)
  {
    std::cerr << "Motor is missing required attributes (`id`, `type` or "
        "`part_id`)." << std::endl;
    throw std::runtime_error("Motor error");
  }

  auto partId = partIdParam->GetAsString();
  auto type = typeParam->GetAsString();
  auto id = idParam->GetAsString();
  MotorPtr motor = this->Motor(_motorSdf, type, partId, id);

  if (not motor)
  {
    std::cerr << "Motor type '" << type << "' is unknown." << std::endl;
    throw std::runtime_error("Motor error");
  }

  return motor;
}
