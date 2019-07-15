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
#include <revolve/gazebo/battery/Battery.h>
namespace revolve
{
  namespace gazebo
  {
    class Motor
    {
        /// \brief Constructor
        /// \brief[in] _model Model identifier
        /// \brief[in] _partId Module identifier
        /// \brief[in] _motorId Motor identifier
        /// \brief[in] _outputs Number of motor outputs
        public: Motor(
        ::gazebo::physics::ModelPtr _model,
        const std::string &_partId,
        const std::string &_motorId,
        const unsigned int _outputs);

        /// \brief Destructor
        public: virtual ~Motor();

        /// \brief Updates the motor based on the attached output of the neural
        /// network.
        /// \param[in,out] output Raw motor update value(s), it is up to the
        /// motor to decide how to interpret this. This is a pointer to an
        /// array of values, out of which the motor should read the first `n`
        /// values if it specifies `n` outputs.
        /// \param[in] step Actuation time in seconds
        public: virtual void Update(
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
    protected:
        ::gazebo::physics::ModelPtr model_;

        /// \brief ID of the body part the motor belongs to
        std::string partId_;

        /// \brief Robot-wide unique motor ID
        std::string motorId_;

        /// \brief Number of output neurons that should be connected to the motor.
        unsigned int outputs_;


        /// \brief Pointer to the battery
        std::shared_ptr<::revolve::gazebo::Battery> battery_;

        /// \brief The id of the consumer
        uint32_t consumerId_;

        friend class MotorFactory;
    };
  } /* namespace gazebo */
} /* namespace tol_robogen */

#endif /* TOL_ROBOGEN_GAZEBO_MOTORS_MOTOR_H_ */
