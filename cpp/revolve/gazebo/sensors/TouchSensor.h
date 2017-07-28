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
* Date: Mar 27, 2015
*
*/

#ifndef REVOLVE_GAZEBO_SENSORS_TOUCHSENSOR_H_
#define REVOLVE_GAZEBO_SENSORS_TOUCHSENSOR_H_

#include <revolve/gazebo/sensors/Sensor.h>

namespace revolve {
namespace gazebo {

class TouchSensor: public Sensor {
public:
	TouchSensor(::gazebo::physics::ModelPtr model, sdf::ElementPtr sensor,
			std::string partId, std::string sensorId);
	virtual ~TouchSensor();

	/**
	 * The touch sensor is boolean; it is either
	 * touching something or it is not. Since
	 * the NN works with floats, we return 0.0
	 * or 1.0.
	 */
	virtual void read(double * input);

	/**
	 * Called when the camera sensor is updated
	 */
	void OnUpdate();

private:
	/**
	 * The contact state at the last update
	 */
	bool lastValue_;

	/**
	 * Sensor dynamically casted to correct type,
	 * so it needs to happen only once.
	 */
	::gazebo::sensors::ContactSensorPtr castSensor_;

    // Pointer to the update connection
    ::gazebo::event::ConnectionPtr updateConnection_;
};

} /* namespace gazebo */
} /* namespace revolve */

#endif /* REVOLVE_GAZEBO_SENSORS_TOUCHSENSOR_H_ */
