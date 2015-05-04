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

MotorFactory::MotorFactory() {}

MotorFactory::~MotorFactory() {}

MotorPtr MotorFactory::create(sdf::ElementPtr motor,
		::gazebo::physics::ModelPtr model, unsigned int /*actuationTime*/) {
	auto typeParam = motor->GetAttribute("type");
	auto jointNameParam = motor->GetAttribute("joint");
	auto partIdParam = motor->GetAttribute("part_id");

	if (!typeParam || !jointNameParam || !partIdParam) {
		std::cerr << "Motor is missing required attributes." << std::endl;
		throw std::runtime_error("Motor error");
	}

	auto jointName = jointNameParam->GetAsString();
	gz::physics::JointPtr joint = model->GetJoint(jointName);

	if (!joint) {
		std::cerr << "Could not locate joint  '" << jointName << "'." << std::endl;
		throw std::runtime_error("Motor error");
	}

	auto partId = partIdParam->GetAsString();

	MotorPtr motorObj;
	auto type = typeParam->GetAsString();

	if ("servo" == type) {
		motorObj.reset(new ServoMotor(model, joint, partId, motor));
	} else {
		std::cerr << "Motor type '" << type <<
				"' is unknown." << std::endl;
		throw std::runtime_error("Motor error");
	}

	return motorObj;
}

} /* namespace gazebo */
} /* namespace tol_robogen */
