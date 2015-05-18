/*
 * VirtualSensor.cpp
 *
 *  Created on: May 6, 2015
 *      Author: elte
 */

#include <revolve/gazebo/sensors/VirtualSensor.h>

namespace revolve {
namespace gazebo {

VirtualSensor::VirtualSensor(::gazebo::physics::ModelPtr model, std::string partId, std::string sensorId, unsigned int inputs):
	model_(model),
	partId_(partId),
	sensorId_(sensorId),
	inputs_(inputs)
{}

VirtualSensor::~VirtualSensor() {}

unsigned int VirtualSensor::inputs() {
	return inputs_;
}

std::string VirtualSensor::partId() {
	return partId_;
}

std::string VirtualSensor::sensorId() {
	return sensorId_;
}

} /* namespace gazebo */
} /* namespace revolve */
