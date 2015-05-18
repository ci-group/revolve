/*
 * MotorFactory.cpp
 *
 *  Created on: Mar 16, 2015
 *      Author: elte
 */

#include <revolve/gazebo/motors/MotorFactory.h>
#include <revolve/gazebo/motors/Motors.h>

#include <cstdlib>

namespace gz = gazebo;

namespace revolve {
namespace gazebo {

MotorFactory::MotorFactory(::gazebo::physics::ModelPtr model):
	model_(model)
{}

MotorFactory::~MotorFactory() {}

MotorPtr MotorFactory::getMotor(sdf::ElementPtr motor, const std::string & type,
								const std::string & partId, const std::string & motorId) {
	MotorPtr motorObj;
	if ("position" == type) {
		motorObj.reset(new PositionMotor(model_, partId, motorId, motor));
	} else if ("velocity" == type) {
		motorObj.reset(new VelocityMotor(model_, partId, motorId, motor));
	}

	return motorObj;
}

MotorPtr MotorFactory::create(sdf::ElementPtr motor) {
	auto typeParam = motor->GetAttribute("type");
	auto partIdParam = motor->GetAttribute("part_id");
	auto idParam = motor->GetAttribute("id");

	if (!typeParam || !partIdParam || !idParam) {
		std::cerr << "Motor is missing required attributes (`id`, `type` or `part_id`)." << std::endl;
		throw std::runtime_error("Motor error");
	}

	auto partId = partIdParam->GetAsString();
	auto type = typeParam->GetAsString();
	auto id = idParam->GetAsString();
	MotorPtr motorObj = this->getMotor(motor, type, partId, id);

	if (!motorObj) {
		std::cerr << "Motor type '" << type <<
				"' is unknown." << std::endl;
		throw std::runtime_error("Motor error");
	}

	return motorObj;
}

} /* namespace gazebo */
} /* namespace revolve */
