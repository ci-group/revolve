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
* Date: May 6, 2015
*
*/

#include <string>

#include <revolve/gazebo/motors/JointMotor.h>

namespace gz = gazebo;

using namespace revolve::gazebo;

/////////////////////////////////////////////////
JointMotor::JointMotor(
    ::gazebo::physics::ModelPtr _model,
    const std::string &_partId,
    const std::string &_motorId,
    sdf::ElementPtr _motor,
    const unsigned int _outputs)
    : Motor(_model, _partId, _motorId, _outputs)
{
  if (not _motor->HasAttribute("joint"))
  {
    std::cerr << "JointMotor requires a `joint` attribute." << std::endl;
    throw std::runtime_error("Motor error");
  }

  auto jointName = _motor->GetAttribute("joint")->GetAsString();
  this->joint_ = _model->GetJoint(jointName);
  if (not this->joint_)
  {
    std::cerr << "Cannot locate joint motor `" << jointName << "`" << std::endl;
    throw std::runtime_error("Motor error");
  }

  this->jointName_ = this->joint_->GetScopedName();
}

/////////////////////////////////////////////////
JointMotor::~JointMotor() = default;
