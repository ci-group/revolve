/*
 * Sensor.h
 *
 *  Created on: Mar 24, 2015
 *      Author: elte
 */

#ifndef REVOLVE_GAZEBO_SENSORS_SENSOR_H_
#define REVOLVE_GAZEBO_SENSORS_SENSOR_H_

#include <gazebo/gazebo.hh>
#include <gazebo/sensors/sensors.hh>

#include <revolve/gazebo/Types.h>

namespace revolve {
namespace gazebo {

class Sensor {
public:
	Sensor(::gazebo::physics::ModelPtr model, ::gazebo::sensors::SensorPtr sensor,
			std::string partId, unsigned int inputNeurons);
	virtual ~Sensor();

	/**
	 * Reads the current value of this sensor into the given network
	 * output array. This should fill the number of output neurons
	 * the sensor specifies to have, i.e. if the sensor specifies 2
	 * output neurons it should fill `networkInput[0]` and `networkInput[1]`
	 */
	virtual void read(float * networkInput) = 0;

	/**
	 * @return The part ID
	 */
	std::string partId();

	/**
	 * @return Number of output neurons on this sensor
	 */
	unsigned int inputNeurons();

	/**
	 * @return The attached Gazebo sensor
	 */
	::gazebo::sensors::SensorPtr gzSensor();

protected:
	/**
	 * The model this motor is part of
	 */
	::gazebo::physics::ModelPtr model_;

	/**
	 * The joint this motor is controlling
	 */
	::gazebo::sensors::SensorPtr sensor_;

	/**
	 * ID of the body part the motor belongs to
	 */
	std::string partId_;

	/**
	 * Number of output neurons on this sensor
	 */
	unsigned int inputNeurons_;
};

} /* namespace gazebo */
} /* namespace revolve */

#endif /* REVOLVE_GAZEBO_SENSORS_SENSOR_H_ */
