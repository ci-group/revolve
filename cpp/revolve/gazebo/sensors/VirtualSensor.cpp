/*
 * VirtualSensor.cpp
 *
 *  Created on: May 6, 2015
 *      Author: elte
 */

#include <revolve/gazebo/sensors/VirtualSensor.h>

namespace revolve {
namespace gazebo {

VirtualSensor::VirtualSensor(::gazebo::physics::ModelPtr model, std::string partId, unsigned int inputNeurons):
	model_(model),
	partId_(partId),
	inputNeurons_(inputNeurons)
{}

VirtualSensor::~VirtualSensor() {}

unsigned int VirtualSensor::inputNeurons() {
	return inputNeurons_;
}

} /* namespace gazebo */
} /* namespace revolve */
