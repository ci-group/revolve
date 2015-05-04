/*
 * Sensor.cpp
 *
 *  Created on: Mar 24, 2015
 *      Author: elte
 */

#include <revolve/gazebo/sensors/Sensor.h>

namespace revolve {
namespace gazebo {

Sensor::Sensor(::gazebo::physics::ModelPtr model, ::gazebo::sensors::SensorPtr sensor,
		std::string partId, unsigned int inputNeurons):
	model_(model),
	sensor_(sensor),
	partId_(partId),
	inputNeurons_(inputNeurons)
{}

Sensor::~Sensor()
{}

std::string Sensor::partId() {
	return partId_;
}

unsigned int Sensor::inputNeurons() {
	return inputNeurons_;
}

::gazebo::sensors::SensorPtr Sensor::gzSensor() {
	return sensor_;
}

} /* namespace gazebo */
} /* namespace tol_robogen */
