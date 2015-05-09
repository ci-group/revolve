/*
 * VirtualSensor.cpp
 *
 *  Created on: May 6, 2015
 *      Author: elte
 */

#include <revolve/gazebo/sensors/VirtualSensor.h>

namespace revolve {
namespace gazebo {

VirtualSensor::VirtualSensor(::gazebo::physics::ModelPtr model, std::string partId, unsigned int inputs):
	model_(model),
	partId_(partId),
	inputs_(inputs)
{}

VirtualSensor::~VirtualSensor() {}

unsigned int VirtualSensor::inputs() {
	return inputs_;
}

} /* namespace gazebo */
} /* namespace revolve */
