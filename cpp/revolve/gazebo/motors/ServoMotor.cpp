/*
 * ServoMotor.cpp
 *
 *  Created on: Mar 5, 2015
 *      Author: elte
 */

#include <revolve/gazebo/motors/ServoMotor.h>

#include <gazebo/math/Rand.hh>

#include <iostream>

namespace gz = gazebo;

namespace revolve {
namespace gazebo {

ServoMotor::ServoMotor(gz::physics::ModelPtr model, std::string partId, sdf::ElementPtr motor):
	JointMotor(model, partId, motor, 1),
	jointController_(model->GetJointController()),
	minVelocity_(0),
	maxVelocity_(0),
	velocityDriven_(false),
	noise_(0)
{
	// Retrieve upper / lower limit from joint set in parent constructor
	upperLimit_ = joint_->GetUpperLimit(0).Radian();
	lowerLimit_ = joint_->GetLowerLimit(0).Radian();

	if (motor->HasAttribute("velocity_driven")) {
		motor->GetAttribute("velocity_driven")->Get(velocityDriven_);
	}

	if (motor->HasElement("rv:pid")) {
		auto pidElem = motor->GetElement("rv:pid");
		auto pid = Motor::createPid(pidElem);

		if (velocityDriven_) {
			jointController_->SetVelocityPID(jointName_, pid);
		} else {
			jointController_->SetPositionPID(jointName_, pid);
		}
	}

	auto noiseParam = motor->GetAttribute("noise");
	if (noiseParam) {
		noiseParam->Get(noise_);
	}

	if (velocityDriven_) {
		if (!motor->HasAttribute("min_velocity") || !motor->HasAttribute("max_velocity")) {
			std::cerr << "Missing servo min/max velocity parameters, "
					"velocity will be zero." << std::endl;
		} else {
			motor->GetAttribute("min_velocity")->Get(minVelocity_);
			motor->GetAttribute("max_velocity")->Get(maxVelocity_);
		}
	}
}

ServoMotor::~ServoMotor() {}

void ServoMotor::update(double * outputs, unsigned int /*step*/) {
	// Just one network output, which is the first
	double networkOutput = outputs[0];

	// Motor noise in range +/- noiseLevel * actualValue
	networkOutput += ((2 * gz::math::Rand::GetDblUniform() * noise_) -
				noise_) * networkOutput;

	if (velocityDriven_) {
		double velocity = minVelocity_ + networkOutput * (maxVelocity_ - minVelocity_);
		jointController_->SetVelocityTarget(jointName_, velocity);
	} else {
		double position = lowerLimit_ + networkOutput * (upperLimit_ - lowerLimit_);
		jointController_->SetPositionTarget(jointName_, position);
	}
}

} /* namespace gazebo */
} /* namespace tol_robogen */
