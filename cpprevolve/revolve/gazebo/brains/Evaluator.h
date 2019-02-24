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
* Author: Matteo De Carlo
*
*/

#ifndef REVOLVEBRAIN_BRAIN_EVALUATOR_H
#define REVOLVEBRAIN_BRAIN_EVALUATOR_H

#include <boost/shared_ptr.hpp>

#include <gazebo/common/common.hh>

namespace revolve
{
  namespace gazebo
  {
    class Evaluator
    {
      /// \brief Constructor
      public: Evaluator(const double _evaluationRate);

      /// \brief Destructor
      public: ~Evaluator();

      /// \brief Initialisation method
      public: void Reset();

      /// \brief Retrieve the fitness
      /// \return A fitness value according to a given formula
      public: double Fitness(std::string controllerType); // {rightTurn, leftTurn, gait}

      /// \brief Update the position
      /// \param[in] _pose Current position of a robot
      public: void Update(const ignition::math::Pose3d &_pose);

      /// \brief Previous position of a robot
      public: ignition::math::Pose3d previousPosition_;

      /// \brief Current position of a robot
      public: ignition::math::Pose3d currentPosition_;

      /// \brief
      private: double evaluationRate_;

      /// \brief Added for targeted locomotion
      private: int iteration;
      private: double bestFitnessLeft;
      private: double bestFitnessRight;
      private: double bestFitnessGait;
      private: double penalty;
      private: double previousAngle;
      private: bool printOutput;
    };
  }
}

#endif  // REVOLVEBRAIN_BRAIN_EVALUATOR_H
