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
* Date: Mar 16, 2015
*
*/

#ifndef REVOLVE_GAZEBO_MOTORS_MOTORFACTORY_H_
#define REVOLVE_GAZEBO_MOTORS_MOTORFACTORY_H_

#include <revolve/gazebo/Types.h>

#include <gazebo/common/common.hh>

namespace revolve {
namespace gazebo {

class MotorFactory {
  public:
  MotorFactory(::gazebo::physics::ModelPtr model);
  virtual ~MotorFactory();

  /**
   * Returns a motor pointer instance from a motor element, part ID and type.
   * This is the convenience wrapper over `create` that has required attributes
   * already checked, usually you should override this when adding new motor types.
   */
  virtual MotorPtr getMotor(sdf::ElementPtr motor, const std::string & type,
                const std::string & motorId, const std::string & partId);

  /**
   * Creates a motor for the given model for the given SDF element.
   */
  virtual MotorPtr create(sdf::ElementPtr motor);

  protected:
  /**
   * Internal reference to the robot model
   */
  ::gazebo::physics::ModelPtr model_;
};

} /* namespace gazebo */
} /* namespace revolve */

#endif /* REVOLVE_GAZEBO_MOTORS_MOTORFACTORY_H_ */
