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
      public: virtual ~Evaluator();

      /// \brief Initialisation method
      public: virtual void Reset(double time);

      /// \brief Retrieve the fitness
      /// \return A fitness value according to a given formula
      public: virtual double Fitness();

      /// \brief Update the position
      /// \param[in] _pose Current position of a robot
      public: virtual void Update(const ignition::math::Pose3d &_pose,
                                  const double time,
                                  const double step);

      /// \brief Previous position of a robot
      protected: ignition::math::Pose3d startPosition_;

      /// \brief Previous position of a robot
      protected: ignition::math::Pose3d previousPosition_;

      /// \brief Current position of a robot
      protected: ignition::math::Pose3d currentPosition_;

      /// \brief
      protected: double evaluationRate_;

      protected: double pathLength;
    };
  }
}

#endif  // REVOLVEBRAIN_BRAIN_EVALUATOR_H
