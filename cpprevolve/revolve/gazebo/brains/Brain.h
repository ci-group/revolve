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

#include <vector>

#include <boost/shared_ptr.hpp>

#include <gazebo/common/common.hh>
#include <gazebo/gazebo.hh>

#include <revolve/gazebo/Types.h>

namespace revolve
{
  namespace gazebo
  {
    class Brain
    {
      /// \brief Constructor
      public: explicit Brain() {}

      /// \brief Destructor
      public: virtual ~Brain() {}

      /// \brief Update step called for the brain.
      /// \param[in] _motors List of motors
      /// \param[in] _sensors List of sensors
      /// \param[in] _time Current simulation time
      /// \param[in] _step Actuation step size in seconds
      public: virtual void Update(
          const std::vector< MotorPtr > &_motors,
          const std::vector< SensorPtr > &_sensors,
          const double _time,
          const double _step) = 0;

      /// \brief Mutex for stepping / updating the network
      protected: boost::mutex networkMutex_;

      /// \brief Transport node
      protected: ::gazebo::transport::NodePtr node_;
    };
  } /* namespace gazebo */
} /* namespace revolve */

#endif /* REVOLVE_GAZEBO_BRAIN_BRAIN_H_ */
