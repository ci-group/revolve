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
* Description: TODO: <Add brief description about file purpose>
* Author: Elte Hupkes
* Date: May 6, 2015
*
*/

#ifndef REVOLVE_GAZEBO_MOTORS_JOINTMOTOR_H_
#define REVOLVE_GAZEBO_MOTORS_JOINTMOTOR_H_

#include <string>

#include <revolve/gazebo/motors/Motor.h>

namespace revolve
{
  namespace gazebo
  {
    class JointMotor
            : public Motor
    {
      public:
      JointMotor(
              ::gazebo::physics::ModelPtr model,
              std::string partId,
              std::string motorId,
              sdf::ElementPtr motor,
              unsigned int outputs);

      virtual ~JointMotor();

      protected:
      /**
       * The joint this motor is controlling
       */
      ::gazebo::physics::JointPtr joint_;

      /**
       * Scoped name of the controlled joint
       */
      std::string jointName_;
    };
  } /* namespace gazebo */
} /* namespace revolve */

#endif /* REVOLVE_GAZEBO_MOTORS_JOINTMOTOR_H_ */
