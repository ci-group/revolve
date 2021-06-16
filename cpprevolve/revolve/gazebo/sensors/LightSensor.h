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
* Author: Elte Hupkes
* Date: Mar 26, 2015
*
*/

#ifndef REVOLVE_GAZEBO_SENSORS_LIGHTSENSOR_H_
#define REVOLVE_GAZEBO_SENSORS_LIGHTSENSOR_H_

#include <string>

#include <revolve/gazebo/sensors/Sensor.h>
#include <gazebo/common/CommonTypes.hh>

namespace revolve
{
  namespace gazebo
  {
    class LightSensor
            : public Sensor
    {
      /// \brief Constructor
      /// \brief[in] _model Model identifier
      /// \brief[in] _sensor Sensor identifier
      /// \brief[in] _partId Module identifier
      /// \brief[in] _sensorId Sensor identifier
      public: LightSensor(
          ::gazebo::physics::ModelPtr _model,
          sdf::ElementPtr _sensor,
          std::string _partId,
          std::string _sensorId);

      /// \brief Returns a float intensity between 0 and 1
      /// \brief[in,out] _input Input value to write on
      public: void read(double *_input) override;

      /// \brief Called when the camera sensor is updated
      public: void OnUpdate();

      /// \brief Sensor dynamically casted to correct type, so it needs to
      /// happen only once.
      private: ::gazebo::sensors::CameraSensorPtr castSensor_;

      /// \brief Size of the data which we determine once
      private: unsigned int dataSize_;

      /// \brief Last calculated average
      private: float lastValue_;

      /// \brief Pointer to the update connection
      private: ::gazebo::event::ConnectionPtr updateConnection_;
    };
  } /* namespace gazebo */
} /* namespace revolve */

#endif /* REVOLVE_GAZEBO_SENSORS_LIGHTSENSOR_H_ */
