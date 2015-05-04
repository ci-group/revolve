/*
 * ImuSensor.cpp
 *
 *  Created on: Mar 24, 2015
 *      Author: elte
 */

#include <revolve/gazebo/sensors/ImuSensor.h>

#include <iostream>
#include <stdexcept>

namespace gz = gazebo;

namespace revolve {
namespace gazebo {

ImuSensor::ImuSensor(::gazebo::physics::ModelPtr model, ::gazebo::sensors::SensorPtr sensor,
		std::string partId):
		Sensor(model, sensor, partId, 6)
{
	this->castSensor_ = boost::dynamic_pointer_cast<gz::sensors::ImuSensor>(sensor);

	if (!this->castSensor_) {
		std::cerr << "Creating an IMU sensor with a non-IMU sensor object." << std::endl;
		throw std::runtime_error("Sensor error");
	}
}

ImuSensor::~ImuSensor() {}

void ImuSensor::read(float * input) {
	auto acc = this->castSensor_->GetLinearAcceleration();
	auto velo = this->castSensor_->GetAngularVelocity();
	input[0] = acc[0];
	input[1] = acc[1];
	input[2] = acc[2];
	input[3] = velo[0];
	input[4] = velo[1];
	input[5] = velo[2];
}

} /* namespace gazebo */
} /* namespace revolve */
