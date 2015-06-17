/*
 * Sensor.cpp
 *
 *  Created on: Mar 24, 2015
 *      Author: elte
 */

#include <revolve/gazebo/sensors/Sensor.h>

namespace gz = gazebo;

namespace revolve {
namespace gazebo {

Sensor::Sensor(::gazebo::physics::ModelPtr model, sdf::ElementPtr sensor,
		std::string partId, std::string sensorId, unsigned int inputs):
	VirtualSensor(model, partId, sensorId, inputs)
{
	if (!sensor->HasAttribute("sensor") || !sensor->HasAttribute("link")) {
		std::cerr << "Sensor is missing required attributes (`link` or `sensor`)." << std::endl;
		throw std::runtime_error("Sensor error");
	}

	auto sensorName = sensor->GetAttribute("sensor")->GetAsString();
	auto linkName = sensor->GetAttribute("link")->GetAsString();

	auto link = model->GetLink(linkName);
	if (!link) {
		std::cerr << "Link '" << linkName << "' for sensor '"
				<< sensorName << "' is not present in model." << std::endl;
		throw std::runtime_error("Sensor error");
	}

	std::string scopedName = link->GetScopedName(true) + "::" + sensorName;
	this->sensor_ = gz::sensors::get_sensor(scopedName);

	if (!this->sensor_) {
		std::cerr << "Sensor with scoped name '" << scopedName
				<< "' could not be found." << std::endl;
		throw std::runtime_error("Sensor error");
	}
}

Sensor::~Sensor()
{}

::gazebo::sensors::SensorPtr Sensor::gzSensor() {
	return sensor_;
}

} /* namespace gazebo */
} /* namespace tol_robogen */
