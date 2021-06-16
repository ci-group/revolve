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
* Description: Sensor class that is connected to an actual Gazebo sensor
* Author: Elte Hupkes
*
*/

#ifndef REVOLVE_GAZEBO_SENSORS_SENSOR_H_
#define REVOLVE_GAZEBO_SENSORS_SENSOR_H_

#include <string>
#include <gazebo/physics/PhysicsTypes.hh>
#include <gazebo/sensors/SensorTypes.hh>
#include <sdf/Element.hh>

#include <revolve/brains/controller/sensors/Sensor.h>

namespace revolve
{
  namespace gazebo
  {
    class Sensor: public ::revolve::Sensor
    {
      /// \brief Constructor
      /// \brief[in] _model Model identifier
      /// \brief[in] _sensor Sensor identifier
      /// \brief[in] _partId Module identifier
      /// \brief[in] _sensorId Sensor identifier
      /// \param[in] _inputs Number of inputs a sensor has
      public: Sensor(
          ::gazebo::physics::ModelPtr _model,
          sdf::ElementPtr _sensor,
          std::string _partId,
          std::string _sensorId,
          unsigned int _inputs);

        /// \return The part ID
    public: const std::string& PartId() const { return partId_; };

        /// \return The ID of the sensor
    public: const std::string& SensorId() const { return sensorId_; };

        /// \return The attached Gazebo sensor
    public: const ::gazebo::sensors::SensorPtr& GzSensor() const { return sensor_; };

        /// \brief The model this sensor is part of
    protected: ::gazebo::physics::ModelPtr model_;

        /// \brief ID of the body part the motor belongs to
    protected: std::string partId_;

        /// \brief ID of the sensor
    protected: std::string sensorId_;

      /// \brief The actual sensor object this sensor is receiving input from
      protected: ::gazebo::sensors::SensorPtr sensor_;
    };
  } /* namespace gazebo */
} /* namespace revolve */

#endif /* REVOLVE_GAZEBO_SENSORS_SENSOR_H_ */
