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

#include "PositionMotor.h"

namespace gz = gazebo;

using namespace revolve::gazebo;

/////////////////////////////////////////////////
PositionMotor::PositionMotor(
    gz::physics::ModelPtr _model,
    const std::string &_partId,
    const std::string &_motorId,
    const sdf::ElementPtr &_motor)
    : JointMotor(std::move(_model), _partId, _motorId, _motor, 1)
    , positionTarget_(0)
    , noise_(0)
{
  // Retrieve upper / lower limit from joint set in parent constructor
  // Truncate ranges to [-pi, pi]
  this->upperLimit_ = std::fmin(M_PI, this->joint_->UpperLimit(0));
  this->lowerLimit_ = std::fmax(-M_PI, this->joint_->LowerLimit(0));
  this->fullRange_ = ((this->upperLimit_ - this->lowerLimit_ + 1e-12) >=
                      (2 * M_PI));

  if (_motor->HasElement("rv:pid"))
  {
    auto pidElem = _motor->GetElement("rv:pid");
    this->pid_ = Motor::CreatePid(pidElem);
  }

  auto noise = _motor->GetAttribute("noise");
  if (noise)
  {
    noise->Get(this->noise_);
  }

  // I've asked this question at the Gazebo forums:
  // http://answers.gazebosim.org/question/9071/joint-target-velocity-with-maximum-force/
  // Until it is answered I'm resorting to calling ODE functions directly
  // to get this to work. This will result in some deprecation warnings.
  // It has the added benefit of not requiring the world update
  // connection though.
  // updateConnection_ = gz::event::Events::ConnectWorldUpdateBegin(boost::bind(
  //   &PositionMotor::OnUpdate, this, _1));

  auto maxEffort = joint_->GetEffortLimit(0);
  joint_->SetParam("fmax", 0, maxEffort);
}

/////////////////////////////////////////////////
PositionMotor::~PositionMotor() = default;

/////////////////////////////////////////////////
// void PositionMotor::OnUpdate(const ::gazebo::common::UpdateInfo info) {
//   DoUpdate(info.simTime);
// }

/////////////////////////////////////////////////
void PositionMotor::Update(
    const double *outputs,
    double /*step*/
    )
{
  // Just one network output, which is the first
  auto output = outputs[0];

  // Motor noise in range +/- noiseLevel * actualValue
  output += ((2 * ignition::math::Rand::DblUniform() * this->noise_) -
             this->noise_) *
            output;

  // Truncate output to [0, 1]
  // Note: Don't actually target the full joint range, this way a low update
  // rate won't mess with the joint constraints as much leading to a more
  // stable system.
  output = std::fmin(std::fmax(1e-5, output), 0.99999);
  this->positionTarget_ = this->lowerLimit_ +
                          (output * (this->upperLimit_ - this->lowerLimit_));

  // Perform the actual motor update
  this->DoUpdate(this->joint_->GetWorld()->SimTime());
}

/////////////////////////////////////////////////
void PositionMotor::DoUpdate(const ::gazebo::common::Time &_simTime)
{
  auto stepTime = _simTime - this->prevUpdateTime_;
  if (stepTime <= 0)
  {
    // Only respond to positive step times
    return;
  }

  this->prevUpdateTime_ = _simTime;
  auto position = this->joint_->Position(0);

  // TODO Make sure normalized angle lies within possible range
  // I get the feeling we might be moving motors outside their
  // allowed range. Also something to be aware of when setting
  // the direction.

  if (this->fullRange_ and std::fabs(position - positionTarget_) > M_PI)
  {
    // Both the position and the position target will be in the range
    // [-pi, pi]. For a full range of motion joint, using an angle +- 2 PI
    // might result in a much shorter required movement. In this case we
    // best correct the current position to something outside the range.
    position += (position > 0 ? -2 * M_PI : 2 * M_PI);
  }


  auto error = position - this->positionTarget_;
  auto cmd = this->pid_.Update(error, stepTime); // angular velocity TODO this is targeted velocity

  if (this->battery_)
  {
      ::gazebo::physics::JointWrench jointWrench = this->joint_->GetForceTorque(0);

      // TODO find which axis to use local or global
      // TODO check the power if it should be positive or negative
      // TODO change this for now im using the absolute value of the power so it always decreases from the joint movements
      double power = -abs(cmd * jointWrench.body1Torque.Length()); // TODO check which torque to use 1 or 2
      this->battery_->SetPowerLoad(this->consumerId_ , power);

  }
  this->joint_->SetParam("vel", 0, cmd);
}
