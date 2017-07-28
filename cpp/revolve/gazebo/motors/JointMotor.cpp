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

#include <revolve/gazebo/motors/JointMotor.h>

namespace gz = gazebo;

namespace revolve {
namespace gazebo {

JointMotor::JointMotor(gz::physics::ModelPtr model, std::string partId,
             std::string motorId, sdf::ElementPtr motor, unsigned int outputs):
  Motor(model, partId, motorId, outputs)
{
  if (!motor->HasAttribute("joint")) {
    std::cerr << "JointMotor requires a `joint` attribute." << std::endl;
    throw std::runtime_error("Motor error");
  }

  auto jointName = motor->GetAttribute("joint")->GetAsString();
  joint_ = model->GetJoint(jointName);
  if (!joint_) {
    std::cerr << "Cannot locate joint motor `" << jointName << "`" << std::endl;
    throw std::runtime_error("Motor error");
  }

  jointName_ = joint_->GetScopedName();
}

JointMotor::~JointMotor() {}

} /* namespace gazebo */
} /* namespace revolve */
