/*
 * VirtualSensor.h
 *
 *  Created on: May 6, 2015
 *      Author: elte
 */

#ifndef REVOLVE_GAZEBO_SENSORS_VIRTUALSENSOR_H_
#define REVOLVE_GAZEBO_SENSORS_VIRTUALSENSOR_H_

#include <gazebo/gazebo.hh>
#include <gazebo/sensors/sensors.hh>

#include <revolve/gazebo/Types.h>

namespace revolve {
namespace gazebo {

class VirtualSensor {
public:
	VirtualSensor(::gazebo::physics::ModelPtr model, std::string partId, unsigned int inputNeurons);
	virtual ~VirtualSensor();

	/**
	 * Reads the current value of this sensor into the given network
	 * output array. This should fill the number of input neurons
	 * the sensor specifies to have, i.e. if the sensor specifies 2
	 * input neurons it should fill `networkInput[0]` and `networkInput[1]`
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

protected:
	/**
	 * The model this motor is part of
	 */
	::gazebo::physics::ModelPtr model_;

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

#endif /* REVOLVE_GAZEBO_SENSORS_VIRTUALSENSOR_H_ */
