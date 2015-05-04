/*
 * SensorFactory.cpp
 *
 *  Created on: Mar 24, 2015
 *      Author: elte
 */

#include <revolve/gazebo/sensors/SensorFactory.h>
#include <revolve/gazebo/sensors/Sensors.h>

#include <stdexcept>
#include <iostream>

namespace gz = gazebo;

namespace revolve {
namespace gazebo {

SensorFactory::SensorFactory()
{}

SensorFactory::~SensorFactory()
{}

SensorPtr SensorFactory::create(sdf::ElementPtr sensor,
		::gazebo::physics::ModelPtr model) {
	auto typeParam = sensor->GetAttribute("type");
	auto nameParam = sensor->GetAttribute("sensor");
	auto partIdParam = sensor->GetAttribute("part_id");
	auto linkParam = sensor->GetAttribute("link");

	if (!typeParam || !nameParam || !partIdParam || !linkParam) {
		std::cerr << "Sensor is missing required attributes." << std::endl;
		throw std::runtime_error("Sensor error");
	}

	auto partId = partIdParam->GetAsString();
	auto sensorName = nameParam->GetAsString();
	auto linkName = linkParam->GetAsString();
	auto link = model->GetLink(linkName);
	if (!link) {
		std::cerr << "Link '" << linkName << "' for sensor '"
				<< sensorName << "' is not present in model." << std::endl;
		throw std::runtime_error("Sensor error");
	}

	std::string scopedName = link->GetScopedName(true) + "::" + sensorName;
	gz::sensors::SensorPtr gzSensor = gz::sensors::get_sensor(scopedName);

	if (!gzSensor) {
		std::cerr << "Sensor with scoped name '" << scopedName
				<< "' could not be found." << std::endl;
		throw std::runtime_error("Sensor error");
	}

	SensorPtr out;

	auto type = typeParam->GetAsString();
	if ("imu" == type) {
		out.reset(new ImuSensor(model, gzSensor, partId));
	} else if ("light" == type) {
		out.reset(new LightSensor(model, gzSensor, partId));
	} else if ("touch" == type) {
		out.reset(new TouchSensor(model, gzSensor, partId));
	}

	if (!out) {
		std::cerr << "Sensor type '" << type << "' is not supported." << std::endl;
		throw std::runtime_error("Sensor error");
	}

	return out;
}

} /* namespace gazebo */
} /* namespace tol_robogen */
