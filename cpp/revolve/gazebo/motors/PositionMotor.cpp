/*
 * ServoMotor.cpp
 *
 *  Created on: Mar 5, 2015
 *      Author: elte
 */

#include <revolve/gazebo/motors/PositionMotor.h>

#include <gazebo/math/Rand.hh>
#include <iostream>

namespace gz = gazebo;

namespace revolve {
namespace gazebo {

PositionMotor::PositionMotor(gz::physics::ModelPtr model, std::string partId,
							 std::string motorId, sdf::ElementPtr motor):
	JointMotor(model, partId, motorId, motor, 1),
	jointController_(model->GetJointController()),
	noise_(0) {
	// Retrieve upper / lower limit from joint set in parent constructor
	upperLimit_ = joint_->GetUpperLimit(0).Radian();
	lowerLimit_ = joint_->GetLowerLimit(0).Radian();

	if (motor->HasElement("rv:pid")) {
		auto pidElem = motor->GetElement("rv:pid");
		auto pid = Motor::createPid(pidElem);

		jointController_->SetPositionPID(jointName_, pid);
	}

	auto noiseParam = motor->GetAttribute("noise");
	if (noiseParam) {
		noiseParam->Get(noise_);
	}
}

PositionMotor::~PositionMotor() { }

void PositionMotor::update(double *outputs, unsigned int /*step*/) {
	// Just one network output, which is the first
	double networkOutput = outputs[0];

	// Motor noise in range +/- noiseLevel * actualValue
	networkOutput += ((2 * gz::math::Rand::GetDblUniform() * noise_) -
					  noise_) * networkOutput;

	double position = lowerLimit_ + networkOutput * (upperLimit_ - lowerLimit_);
	jointController_->SetPositionTarget(jointName_, position);
}

} /* namespace gazebo */
} /* namespace revolve */
