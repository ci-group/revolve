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
* Description: Sensor that reads the battery state out of the model SDF
* Author: Elte Hupkes
*
*/

#ifndef REVOLVE_BATTERYSENSOR_H
#define REVOLVE_BATTERYSENSOR_H

#include <string>

#include "VirtualSensor.h"

namespace revolve
{
  namespace gazebo
  {
    class BatterySensor
        : public VirtualSensor
    {
      /// \brief Constructor
      /// \brief[in] _model Model identifier
      /// \brief[in] _partId Module identifier
      /// \brief[in] _sensorId Sensor identifier
      public: BatterySensor(
          ::gazebo::physics::ModelPtr _model,
          std::string _partId,
          std::string _sensorId);

      /// \brief Reads the battery value
      /// \param[in,out] _input: Input parameter of the sensor
      public: virtual void Read(double *_input);

      /// \brief SDF battery
      protected: sdf::ElementPtr battery_;
    };
  }
}

#endif  // REVOLVE_BATTERYSENSOR_H
