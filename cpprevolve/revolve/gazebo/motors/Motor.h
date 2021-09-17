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
* Description: Motor base class
* Author: Elte Hupkes
*
*/

#ifndef REVOLVE_GAZEBO_MOTORS_MOTOR_H_
#define REVOLVE_GAZEBO_MOTORS_MOTOR_H_

#include <string>

#include <gazebo/gazebo.hh>
#include <gazebo/physics/physics.hh>

#include <revolve/gazebo/Types.h>
#include <revolve/brains/controller/actuators/Actuator.h>

namespace revolve
{
  namespace gazebo
  {
    class Motor : public ::revolve::Actuator
    {
      /// \brief Constructor
      /// \brief[in] _model Model identifier
      /// \brief[in] _partId Module identifier
      /// \brief[in] _motorId Motor identifier
      /// \brief[in] _outputs Number of motor outputs
    public: Motor (
          ::gazebo::physics::ModelPtr _model,
          const std::string &_partId,
          const std::string &_motorId,
          unsigned int _outputs,
          const std::string &_coordinates);

      /// \brief Destructor
      public: virtual ~Motor();

      /// \brief Updates the motor based on the attached output of the neural
      /// network.
      /// \param[in,out] output Raw motor update value(s), it is up to the
      /// motor to decide how to interpret this. This is a pointer to an
      /// array of values, out of which the motor should read the first `n`
      /// values if it specifies `n` outputs.
      /// \param[in] step Actuation time in seconds
      public: void write(
          const double *_output,
          double _step) = 0;

      /// \brief Retrieve the ID
      /// \return The part ID
      public: std::string PartId();

      /// \return The full ID of the motor (should be unique in the robot)
      public: std::string MotorId();

      /// \return Number of output neurons connected to this motor
      public: unsigned int Outputs();

      /// \brief Create PID element
      /// \param pid Pointer to the rv:pid element
      /// \return Gazebo PID
      public: static ::gazebo::common::PID CreatePid(sdf::ElementPtr _sdfPID);

      /// \brief The model this motor is part of
      protected: ::gazebo::physics::ModelPtr model_;

      /// \brief ID of the body part the motor belongs to
      protected: std::string partId_;

      /// \brief Robot-wide unique motor ID
      protected: std::string motorId_;
    };
  } /* namespace gazebo */
} /* namespace tol_robogen */

#endif /* TOL_ROBOGEN_GAZEBO_MOTORS_MOTOR_H_ */
