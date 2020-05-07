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

#include <string>

#include <gazebo/common/common.hh>

#include <revolve/gazebo/Types.h>

#include <revolve/gazebo/battery/Battery.h>

namespace revolve
{
  namespace gazebo
  {
    class MotorFactory
    {
      /// \brief Constructor
      /// \brief[in] _model Model identifier
      /// \brief[in] _partId Module identifier
      /// \brief[in] _motorId Motor identifier
      /// \brief[in] _outputs Number of motor outputs
      public: explicit MotorFactory(::gazebo::physics::ModelPtr model);

      /// \brief Destructor
      public: virtual ~MotorFactory();

      /// \brief Returns a motor pointer instance from a motor element, part
      /// ID and type. This is the convenience wrapper over `create` that has
      /// required attributes already checked, usually you should override
      /// this when adding new motor types.
      public: virtual MotorPtr Motor(
        sdf::ElementPtr _motorSdf,
        const std::string &_type,
        const std::string &_partId,
        const std::string &_motorId,
        std::shared_ptr<::revolve::gazebo::Battery> battery);

      /// \brief Creates a motor for the given model for the given SDF element.
      public: virtual MotorPtr Create(sdf::ElementPtr _motorSdf, std::shared_ptr<::revolve::gazebo::Battery>);

      /// \brief Internal reference to the robot model
      protected: ::gazebo::physics::ModelPtr model_;
    };
  } /* namespace gazebo */
} /* namespace revolve */

#endif /* REVOLVE_GAZEBO_MOTORS_MOTORFACTORY_H_ */
