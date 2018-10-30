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
 * Date: 28/10/2018
 *
 */

#ifndef REVOLVE_THYMIOBRAIN_H
#define REVOLVE_THYMIOBRAIN_H

#include "Brain.h"


namespace revolve
{
  namespace gazebo
  {
    class ThymioBrain
        : public Brain
    {
      /// \brief The RLPower constructor reads out configuration file,
      /// deretmines which algorithm type to apply and initialises new policy.
      /// \param[in] _modelName: name of a robot
      /// \param[in] _node: configuration file
      /// \param[in] _motors: vector list of robot's actuators
      /// \param[in] _sensors: vector list of robot's sensors
      /// \return pointer to the RLPower class object
      public: ThymioBrain(
          ::gazebo::physics::ModelPtr _model,
          sdf::ElementPtr _node,
          std::vector< MotorPtr > &_motors,
          std::vector< SensorPtr > &_sensors);

      /// \brief Destructor
      public: ~ThymioBrain() override;

      /// \brief  Method for updating sensors readings, actuators positions,
      /// ranked list of policies and generating new policy
      /// \param[in] _motors: vector list of robot's actuators
      /// \param[in] _sensors: vector list of robot's sensors
      /// \param[in] _time:
      /// \param[in] _step:
      public: void Update(
          const std::vector< MotorPtr > &_motors,
          const std::vector< SensorPtr > &_sensors,
          double _time,
          double _step) override;

      /// \brief Name of the robot
      private: ::gazebo::physics::ModelPtr robot_;
    };
  }
}

#endif //REVOLVE_THYMIOBRAIN_H
