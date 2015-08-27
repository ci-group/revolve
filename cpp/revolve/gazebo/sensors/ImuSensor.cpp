/*
 * ImuSensor.cpp
 *
 *  Created on: Mar 24, 2015
 *      Author: elte
 */

#include "ImuSensor.h"

#include <iostream>
#include <stdexcept>

namespace gz = gazebo;

namespace revolve {
namespace gazebo {

ImuSensor::ImuSensor(::gazebo::physics::ModelPtr model, sdf::ElementPtr sensor,
		std::string partId, std::string sensorId):
		Sensor(model, sensor, partId, sensorId, 6)
{
	this->castSensor_ = boost::dynamic_pointer_cast<gz::sensors::ImuSensor>(this->sensor_);

	if (!this->castSensor_) {
		std::cerr << "Creating an IMU sensor with a non-IMU sensor object." << std::endl;
		throw std::runtime_error("Sensor error");
	}

	// Initialize all initial values to zero
	memset(lastValues_, 0, sizeof(lastValues_));

	// Add update connection that will produce new value
	this->updateConnection_ = this->castSensor_->ConnectUpdated(boost::bind(&ImuSensor::OnUpdate, this));
}

ImuSensor::~ImuSensor() {}

void ImuSensor::OnUpdate() {
	// Store the recorded values
	auto acc = this->castSensor_->LinearAcceleration();
	auto velo = this->castSensor_->AngularVelocity();
	lastValues_[0] = acc[0];
	lastValues_[1] = acc[1];
	lastValues_[2] = acc[2];
	lastValues_[3] = velo[0];
	lastValues_[4] = velo[1];
	lastValues_[5] = velo[2];
}

void ImuSensor::read(double * input) {
	// Copy our values to the input array
	memcpy(input, lastValues_, sizeof(lastValues_));
}

} /* namespace gazebo */
} /* namespace revolve */
