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

#include <revolve/gazebo/motors/JointMotor.h>
#include <gazebo/common/common.hh>

namespace revolve {
namespace gazebo {

class VelocityMotor : public JointMotor {
  public:
    /**
     * @param The model the motor is contained in
     * @param The joint driven by the motor
     * @param The part ID the motor belongs to
     * @param Whether the motor is velocity driven (the alternative is position driven)
     * @param The derivative gain of the motor's PID controller
     */
    VelocityMotor(::gazebo::physics::ModelPtr model, std::string partId, std::string motorId, sdf::ElementPtr motor);

    virtual ~VelocityMotor();

    /**
     * The velocity motor update action takes an output between 0 and 1 and
     * converts it to a velocity target between the minimum and maximum
     * velocity set by the motor.
     */
    virtual void update(double *outputs, double step);

  protected:
    // World update event function
//    void OnUpdate(const ::gazebo::common::UpdateInfo info);

    // Perform the actual update given the step size
    void DoUpdate(const ::gazebo::common::Time &simTime);

    // Store update event pointer
//    ::gazebo::event::ConnectionPtr updateConnection_;

    // Last update time, used to determine update step time
    ::gazebo::common::Time prevUpdateTime_;

  // The current velocity target
  double velocityTarget_;

    // Velocity limits
    double minVelocity_;
    double maxVelocity_;

    // Motor noise
    double noise_;

    /**
     * PID for this velocity motor
     */
    ::gazebo::common::PID pid_;
};

} // namespace gazebo
} // namespace revolve


#endif //REVOLVE_VELOCITYMOTOR_H
