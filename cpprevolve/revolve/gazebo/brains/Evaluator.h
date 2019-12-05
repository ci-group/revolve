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

#pragma once

#include <boost/shared_ptr.hpp>

#include <gazebo/common/common.hh>
#include <revolve/brains/learner/Evaluator.h>

namespace revolve {
namespace gazebo {
class Evaluator : public ::revolve::Evaluator
{
public:
    /// \brief Constructor
    Evaluator(const double _evaluationRate,
              const double step_saving_rate = 0.1);

    /// \brief Destructor
    ~Evaluator();

    /// \brief Initialisation method
    void reset() override;

    /// \brief Retrieve the fitness
    /// \return A fitness value according to a given formula
    double fitness() override;

    double measure_distance(
            const ignition::math::Pose3d &_pose1,
            const ignition::math::Pose3d &_pose2);

    /// brief Specifies locomotion type
    std::string locomotion_type;

    /// \brief Update the position
    /// \param[in] pose Current position of a robot
    void simulation_update(const ignition::math::Pose3d &pose,
                           double time,
                           double step);

protected:
    /// \brief start position of a robot
    ignition::math::Pose3d start_position_;

    /// \brief Previous position of a robot
    ignition::math::Pose3d previous_position_;

    /// \brief Current position of a robot
    ignition::math::Pose3d current_position_;

    /// \brief
    double evaluation_rate_;

    double path_length = 0.0;

    double last_step_time;
    double step_saving_rate;
    std::vector <ignition::math::Pose3d> step_poses;
};

}
}
