/*
 * TouchSensor.cpp
 *
 *  Created on: Mar 27, 2015
 *      Author: elte
 */

#include <revolve/gazebo/sensors/TouchSensor.h>

#include <boost/bind.hpp>

namespace gz = gazebo;

namespace revolve {
namespace gazebo {

TouchSensor::TouchSensor(::gazebo::physics::ModelPtr model, sdf::ElementPtr sensor,
		std::string partId, std::string sensorId):
		Sensor(model, sensor, partId, sensorId, 1),
		lastValue_(false)
{
	this->castSensor_ = boost::dynamic_pointer_cast<gz::sensors::ContactSensor>(this->sensor_);

	if (!this->castSensor_) {
		std::cerr << "Creating a touch sensor with a non-contact sensor object." << std::endl;
		throw std::runtime_error("Sensor error");
	}

	// Sensor must always update
	this->castSensor_->SetActive(true);

	// Add update connection that will produce new value
	this->updateConnection_ = this->sensor_->ConnectUpdated(boost::bind(&TouchSensor::OnUpdate, this));
}

TouchSensor::~TouchSensor()
{}

void TouchSensor::OnUpdate() {
	auto contacts = this->castSensor_->GetContacts();
	this->lastValue_ = contacts.contact_size() > 0;
}

void TouchSensor::read(double * input) {
	input[0] = lastValue_ ? 1 : 0;
}

} /* namespace gazebo */
} /* namespace revolve */
