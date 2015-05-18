/*
 * LightSensor.h
 *
 *  Created on: Mar 26, 2015
 *      Author: elte
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
