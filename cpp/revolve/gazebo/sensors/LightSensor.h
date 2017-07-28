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

#include <revolve/gazebo/sensors/Sensor.h>

namespace revolve {
namespace gazebo {

class LightSensor: public Sensor {
public:
	LightSensor(::gazebo::physics::ModelPtr model, sdf::ElementPtr sensor,
			std::string partId, std::string sensorId);
	virtual ~LightSensor();

	/**
	 * Returns a float intensity between 0 and 1
	 */
	virtual void read(double * input);

	/**
	 * Called when the camera sensor is updated
	 */
	void OnUpdate();

private:
	/**
	 * Sensor dynamically casted to correct type,
	 * so it needs to happen only once.
	 */
	::gazebo::sensors::CameraSensorPtr castSensor_;

	/**
	 * Size of the data which we determine once
	 */
	unsigned int dataSize_;

	/**
	 * Last calculated average
	 */
	float lastValue_;

    // Pointer to the update connection
    ::gazebo::event::ConnectionPtr updateConnection_;
};

} /* namespace gazebo */
} /* namespace revolve */

#endif /* REVOLVE_GAZEBO_SENSORS_LIGHTSENSOR_H_ */
