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

#include <cmath>
#include <string>

#include "VelocityMotor.h"
#include "JointMotor.h"

namespace gz = gazebo;

using namespace revolve::gazebo;

VelocityMotor::VelocityMotor(
      ::gazebo::physics::ModelPtr _model,
      const std::string &_partId,
      const std::string &_motorId,
      sdf::ElementPtr _motor,
      const std::string &_coordinates)
    : JointMotor(_model, _partId, _motorId, _motor, 1, _coordinates)
    , velocityTarget_(0)
    , noise_(0)
{
  if (_motor->HasElement("rv:pid"))
  {
    auto pidElem = _motor->GetElement("rv:pid");
    this->pid_ = Motor::CreatePid(pidElem);
  }

  if (not _motor->HasAttribute("min_velocity") or
      not _motor->HasAttribute("max_velocity"))
  {
    std::cerr << "Missing servo min/max velocity parameters, "
        "velocity will be zero." << std::endl;
    this->minVelocity_ = this->maxVelocity_ = 0;
  }
  else
  {
    _motor->GetAttribute("min_velocity")->Get(this->minVelocity_);
    _motor->GetAttribute("max_velocity")->Get(this->maxVelocity_);
  }

  // I've asked this question at the Gazebo forums: https://tinyurl.com/y7he7y8l
  // Until it is answered I'm resorting to calling ODE functions directly
  // to get this to work. This will result in some deprecation warnings.
  // The update connection is no longer needed though.;
  double maxEffort = this->joint_->GetEffortLimit(0);
  this->joint_->SetParam("fmax", 0, maxEffort);
}

VelocityMotor::~VelocityMotor()
{
}

void VelocityMotor::Update(
    const double *outputs,
    double /*step*/)
{
  // Just one network output, which is the first
  auto output = outputs[0];

  // Motor noise in range +/- noiseLevel * actualValue
  output += ((2 * ignition::math::Rand::DblUniform() * this->noise_) -
             this->noise_) *
            output;

  // Truncate output to [0, 1]
  output = std::fmax(std::fmin(output, 1), 0);
  this->velocityTarget_ = minVelocity_ + output * (maxVelocity_ - minVelocity_);
  this->DoUpdate(this->joint_->GetWorld()->SimTime());
}

void VelocityMotor::DoUpdate(const ::gazebo::common::Time &/*simTime*/)
{
  // I'm caving for now and am setting ODE parameters directly.
  // See https://tinyurl.com/y7he7y8l
  this->joint_->SetParam("vel", 0, this->velocityTarget_);
}
