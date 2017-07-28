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
* Description: Specifies a utility `Brain` base class. If your brain doesn't
*              fit this model, something else can easily be used by simply
*              ignoring the default brain behavior in the `RobotController`.
* Author: Elte Hupkes
*
*/

#ifndef REVOLVE_GAZEBO_BRAIN_BRAIN_H_
#define REVOLVE_GAZEBO_BRAIN_BRAIN_H_

#include <revolve/gazebo/Types.h>
#include <boost/shared_ptr.hpp>
#include <gazebo/common/common.hh>

namespace revolve {
namespace gazebo {

class Brain {
public:
  Brain() {};
  virtual ~Brain() {};

  /**
   * Update step called for the brain.
   *
   * @param List of motors
   * @param List of sensors
   * @param Current simulation time
   * @param Actuation step size in seconds
   */
  virtual void update(const std::vector< MotorPtr > & motors, const std::vector< SensorPtr > & sensors,
        double t, double step) = 0;
};

} /* namespace gazebo */
} /* namespace revolve */

#endif /* REVOLVE_GAZEBO_BRAIN_BRAIN_H_ */
