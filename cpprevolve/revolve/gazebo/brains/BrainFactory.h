/*
 * Copyright (C) 2015-2018 Vrije Universiteit Amsterdam
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
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
 * Author: Milan Jelisavcic
 * Date: December 23, 2018
 *
 */

#ifndef REVOLVE_GAZEBO_BRAINS_BRAINFACTORY_H_
#define REVOLVE_GAZEBO_BRAINS_BRAINFACTORY_H_

#include <string>

#include <gazebo/common/common.hh>

#include <revolve/gazebo/Types.h>

namespace revolve
{
  namespace gazebo
  {
    class BrainFactory
    {
      /// \brief Constructor
      /// \param[in] _model Model identifier
      public: explicit BrainFactory(::gazebo::physics::ModelPtr _model);

      /// \brief Destructor
      public: virtual ~BrainFactory();

      /// \brief Returns a brain pointer reference from a brain element.
      /// This is the convenience wrapper over `create` that has required
      /// attributes already checked, usually you should override this when
      /// adding new brain types.
      public: virtual BrainPtr Brain(
          sdf::ElementPtr _brainSdf,
          const std::vector< MotorPtr > &_motors,
          const std::vector< SensorPtr > &_sensors);

      /// \brief Creates a brain for the given model for the given SDF element.
      public: virtual BrainPtr Create(
          sdf::ElementPtr _brainSdf,
          const std::vector< MotorPtr > &_motors,
          const std::vector< SensorPtr > &_sensors);

      /// \brief Internal reference to the robot model
      protected: ::gazebo::physics::ModelPtr model_;
    };
  }
}

#endif // REVOLVE_GAZEBO_BRAINS_BRAINFACTORY_H_
