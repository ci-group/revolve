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
* Description: Velocity based (servo) motor
* Author: Elte Hupkes
*
*/

#ifndef REVOLVE_VELOCITYMOTOR_H
#define REVOLVE_VELOCITYMOTOR_H

#include <string>

#include <gazebo/common/common.hh>

#include <revolve/gazebo/motors/JointMotor.h>

namespace revolve {
namespace gazebo {
class VelocityMotor : public JointMotor {
public:
    /// \brief Constructor
    /// \param model The model the motor is contained in
    /// \param The joint driven by the motor
    /// \param partId The part ID the motor belongs to
    /// \param motorId Whether the motor is velocity driven (the
    /// alternative is position driven)
    /// \param motor The derivative gain of the motor's PID controller
    VelocityMotor(
            ::gazebo::physics::ModelPtr _model,
            const std::string &_partId,
            const std::string &_motorId,
            sdf::ElementPtr _motor,
            const std::string &_coordinates);

    /// \brief Destructor
    ~VelocityMotor() override;

    /// \brief The velocity motor update action takes an output between 0
    /// and 1 and converts it to a velocity target between the minimum and
    /// maximum velocity set by the motor.
    /// \param[in,out] outputs
    /// \param[in] step
    void write(
            const double *outputs,
            double step) override;

    double Current_State(Actuator::StateType type) override;

protected:
/// \brief World update event function
//    void OnUpdate(const ::gazebo::common::UpdateInfo info);

    /// \brief Perform the actual update given the step size
    void DoUpdate(const ::gazebo::common::Time &simTime);

    /// \brief Store update event pointer
//    ::gazebo::event::ConnectionPtr updateConnection_;

    /// \brief Last update time, used to determine update step time
    ::gazebo::common::Time prevUpdateTime_;

    /// \brief The current velocity target
    double velocityTarget_;

    /// \brief Velocity limits
    double minVelocity_;

    /// \brief
    double maxVelocity_;

    /// \brief Motor noise
    double noise_;

    /// \brief PID for this velocity motor
    ::gazebo::common::PID pid_;
};
}  // namespace gazebo
}  // namespace revolve

#endif  // REVOLVE_VELOCITYMOTOR_H
