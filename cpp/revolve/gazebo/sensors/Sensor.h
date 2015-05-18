/*
 * Sensor class that is connected to an actual Gazebo sensor
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
