/*
 * SensorFactory.cpp
 *
 *  Created on: Mar 24, 2015
 *      Author: elte
 */

#include "revolve/gazebo/sensors/SensorFactory.h"
#include "revolve/gazebo/sensors/Sensors.h"

namespace gz = gazebo;

namespace revolve {
namespace gazebo {

SensorFactory::SensorFactory(gz::physics::ModelPtr model):
	model_(model)
{}

SensorFactory::~SensorFactory()
{}

SensorPtr SensorFactory::getSensor(sdf::ElementPtr sensor,
								   const std::string& type,
								   const std::string& partId,
								   const std::string& sensorId)
{
	SensorPtr out;
	if ("imu" == type) {
		out.reset(new ImuSensor(this->model_, sensor, partId, sensorId));
	} else if ("light" == type) {
		out.reset(new LightSensor(this->model_, sensor, partId, sensorId));
	} else if ("touch" == type) {
		out.reset(new TouchSensor(this->model_, sensor, partId, sensorId));
	} else if ("basic_battery" == type) {
		out.reset(new BatterySensor(this->model_, partId, sensorId));
	} else if ("point_intensity" == type) {
		out.reset(new PointIntensitySensor(sensor, this->model_, partId, sensorId));
	}

	return out;
}

SensorPtr SensorFactory::create(sdf::ElementPtr sensor)
{
	auto typeParam = sensor->GetAttribute("type");
	auto partIdParam = sensor->GetAttribute("part_id");
	auto idParam = sensor->GetAttribute("id");

	if (!typeParam || !partIdParam || !idParam) {
		std::cerr << "Sensor is missing required attributes (`id`, `type` or `part_id`)." << std::endl;
		throw std::runtime_error("Sensor error");
	}

	auto partId = partIdParam->GetAsString();
	auto type = typeParam->GetAsString();
	auto id = idParam->GetAsString();

	SensorPtr out = this->getSensor(sensor, type, partId, id);
	if (!out) {
		std::cerr << "Sensor type '" << type << "' is not supported." << std::endl;
		throw std::runtime_error("Sensor error");
	}

	return out;
}

} /* namespace gazebo */
} /* namespace revolve */
