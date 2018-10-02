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
* Description: Sensor that measures the intensity this robot feels of a
*              radiating point somewhere in the distance. This is
*              parameterised by a couple of values. Say the distance of the
*              center of mass of the robot to the intensity source is `d`, we
*              then have parameters I+, `r` and `a` such that for the measured
*              intensity I it holds that:
*
*              I = I+				if d <= r
*              I = I+ * (r/d)^2		otherwise
*
*              This corresponds to a quadratic decrease with `r` - intensity
*              is maximal at `r`, 1/4 at 2r, 1/9 at 3r, etc.
* Author: Elte Hupkes
*
*/

#ifndef REVOLVE_POINTINTENSITYSENSOR_H
#define REVOLVE_POINTINTENSITYSENSOR_H

#include <string>

#include "VirtualSensor.h"

namespace revolve
{
  namespace gazebo
  {
    class PointIntensitySensor
            : public VirtualSensor
    {
      /// \brief Constructor
      /// \brief[in] _model Model identifier
      /// \brief[in] _sensor Sensor identifier
      /// \brief[in] _partId Module identifier
      /// \brief[in] _sensorId Sensor identifier
      public: PointIntensitySensor(
          sdf::ElementPtr _sensor,
          ::gazebo::physics::ModelPtr _model,
          std::string _partId,
          std::string _sensorId);

      /// \brief Reads the battery value
      /// \brief[in,out] _input Input value to write on
      public: virtual void Read(double *_input);

      /// \brief The point to which proximity should be returned
      protected: ::gazebo::math::Vector3 point_;

      /// \brief The value of the input neuron of this sensor is calculated
      /// from the distance with the function:
      /// `a / (distance**b)`
      /// Where it will be made sure that the output is between 0 and a.
      protected: double maxInput_;

      /// \brief Radius distance
      protected: double r_;
    };
  }
}

#endif  // REVOLVE_POINTINTENSITYSENSOR_H
