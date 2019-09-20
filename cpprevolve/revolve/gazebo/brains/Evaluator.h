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
      public: Evaluator(const double _evaluationRate,
                        const double step_saving_rate = 0.1);

      /// \brief Destructor
      public: ~Evaluator();

      /// \brief Initialisation method
      public: void Reset();

      /// \brief Retrieve the fitness
      /// \return A fitness value according to a given formula
      public: double Fitness();

      public: double measure_distance(
          const ignition::math::Pose3d &_pose1,
          const ignition::math::Pose3d &_pose2);

      /// brief Specifies locomotion type
      public: std::string locomotion_type;

      /// \brief Update the position
      /// \param[in] _pose Current position of a robot
      public: void Update(const ignition::math::Pose3d &_pose,
                          const double time,
                          const double step);

      /// \brief start position of a robot
      protected: ignition::math::Pose3d start_position_;

      /// \brief Previous position of a robot
      protected: ignition::math::Pose3d previous_position_;

      /// \brief Current position of a robot
      protected: ignition::math::Pose3d current_position_;

      /// \brief
      protected: double evaluation_rate_;

      protected: double path_length = 0.0;

      protected: double last_step_time;
      protected: double step_saving_rate;
      protected: std::vector<ignition::math::Pose3d> step_poses;
      //      public: double current_dist_pro = 0.0;
    public: std::string directory_name = "";
    };
  }
}

#endif  // REVOLVEBRAIN_BRAIN_EVALUATOR_H
