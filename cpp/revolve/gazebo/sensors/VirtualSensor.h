/*
 * The `VirtualSensor` is the base class for all Sensors, it defines
 * the sensor interface but is not necessarily connected to anything
 * concrete in the simulation.
 *
 * @author Elte Hupkes
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
	VirtualSensor(::gazebo::physics::ModelPtr model, std::string partId, std::string sensorId, unsigned int inputs);
	virtual ~VirtualSensor();

	/**
	 * Reads the current value of this sensor into the given network
	 * output array. This should fill the number of input neurons
	 * the sensor specifies to have, i.e. if the sensor specifies 2
	 * input neurons it should fill `input[0]` and `input[1]`
	 */
	virtual void read(double * input) = 0;

	/**
	 * @return The part ID
	 */
	std::string partId();

	/**
	 * @return The ID of the sensor
	 */
	std::string sensorId();

	/**
	 * @return Number of inputs this sensor generates
	 */
	unsigned int inputs();

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
	 * ID of the sensor
	 */
	std::string sensorId_;

	/**
	 * Number of inputs this sensor generates
	 */
	unsigned int inputs_;
};

} /* namespace gazebo */
} /* namespace revolve */

#endif /* REVOLVE_GAZEBO_SENSORS_VIRTUALSENSOR_H_ */
