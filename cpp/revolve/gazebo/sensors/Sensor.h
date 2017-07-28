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

#include <revolve/gazebo/sensors/VirtualSensor.h>

namespace revolve {
namespace gazebo {

class Sensor : public VirtualSensor {
public:
	Sensor(::gazebo::physics::ModelPtr model, sdf::ElementPtr sensor,
			std::string partId, std::string sensorId, unsigned int inputs);
	virtual ~Sensor();

	/**
	 * @return The attached Gazebo sensor
	 */
	::gazebo::sensors::SensorPtr gzSensor();

protected:
	/**
	 * The actual sensor object this sensor is receiving
	 * input from.
	 */
	::gazebo::sensors::SensorPtr sensor_;
};

} /* namespace gazebo */
} /* namespace revolve */

#endif /* REVOLVE_GAZEBO_SENSORS_SENSOR_H_ */
