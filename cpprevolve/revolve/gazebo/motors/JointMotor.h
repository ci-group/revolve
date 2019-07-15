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

namespace revolve {
namespace gazebo {

class JointMotor : public Motor {
    /// \brief Constructor
    /// \brief[in] _model Model identifier
    /// \brief[in] _partId Module identifier
    /// \brief[in] _motorId Motor identifier
    /// \brief[in] _outputs Number of motor outputs
public:
    JointMotor(
            ::gazebo::physics::ModelPtr _model,
            const std::string &_partId,
            const std::string &_motorId,
            sdf::ElementPtr _motor,
            const unsigned int _outputs);

    /// \brief Destructor
public:
    virtual ~JointMotor();

    /// \brief The joint this motor is controlling
protected:
    ::gazebo::physics::JointPtr joint_;

    /// \brief  Scoped name of the controlled joint
    std::string jointName_;
};
} /* namespace gazebo */
} /* namespace revolve */

#endif /* REVOLVE_GAZEBO_MOTORS_JOINTMOTOR_H_ */
