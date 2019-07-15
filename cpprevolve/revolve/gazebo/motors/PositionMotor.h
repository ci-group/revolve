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
* Description: Position based (servo) motor
* Author: Elte Hupkes
*
*/

#ifndef REVOLVE_GAZEBO_POSITIONMOTOR_H_
#define REVOLVE_GAZEBO_POSITIONMOTOR_H_

#include <string>

#include <gazebo/common/common.hh>

#include <revolve/gazebo/motors/JointMotor.h>

namespace revolve
{
  namespace gazebo
  {
    class PositionMotor
            : public JointMotor
    {
      /// \brief Constructor
      /// \param The model the motor is contained in
      /// \param The joint driven by the motor
      /// \param The part ID the motor belongs to
      /// \param Whether the motor is velocity driven (the alternative is
      /// position driven)
      /// \param The derivative gain of the motor's PID controller
      public: PositionMotor(
          ::gazebo::physics::ModelPtr _model,
          const std::string &_partId,
          const std::string &_motorId,
          const sdf::ElementPtr &_motor);

      /// \brief Destructor
      public: virtual ~PositionMotor() override;

      /// \brief
      public: virtual void Update(
          const double *_outputs,
          double _step) override;

      /// \brief World update event function
//      protected: void OnUpdate(const ::gazebo::common::UpdateInfo info);

      /// \brief Perform the actual update given the step size
      protected: void DoUpdate(const ::gazebo::common::Time &_simTime);

      /// \brief Store update event pointer
      protected: ::gazebo::event::ConnectionPtr updateConnection_;

      /// \brief Last update time, used to determine update step time
      protected: ::gazebo::common::Time prevUpdateTime_;

      /// \brief Current position target
      protected: double positionTarget_;

      /// \brief Upper and lower position limits
      protected: double lowerLimit_;

      /// \brief
      protected: double upperLimit_;

      /// \brief Whether this joint can achieve a full range of motion,
      /// meaning it can flip from a positive to a negative angle. This is
      /// set to true whenever the total range is >/ 2 pi.
      protected: bool fullRange_;

      /// \brief Motor noise
      protected: double noise_;

      /// \brief PID that controls this motor
      protected: ::gazebo::common::PID pid_;
    };
  } /* namespace gazebo */
} /* namespace revolve */

#endif /* REVOLVE_GAZEBO_POSITIONMOTOR_H_ */
