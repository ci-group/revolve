/*
 * JointMotor.cpp
 *
 *  Created on: May 6, 2015
 *      Author: elte
 */

#include <revolve/gazebo/motors/JointMotor.h>

namespace gz = gazebo;

namespace revolve {
namespace gazebo {

JointMotor::JointMotor(gz::physics::ModelPtr model, std::string partId,
					   std::string motorId, sdf::ElementPtr motor, unsigned int outputs):
	Motor(model, partId, motorId, outputs)
{
	if (!motor->HasAttribute("joint")) {
		std::cerr << "JointMotor requires a `joint` attribute." << std::endl;
		throw std::runtime_error("Motor error");
	}

	auto jointName = motor->GetAttribute("joint")->GetAsString();
	joint_ = model->GetJoint(jointName);
	if (!joint_) {
		std::cerr << "Cannot locate joint motor `" << jointName << "`" << std::endl;
		throw std::runtime_error("Motor error");
	}

	jointName_ = joint_->GetScopedName();
}

JointMotor::~JointMotor() {}

} /* namespace gazebo */
} /* namespace revolve */
