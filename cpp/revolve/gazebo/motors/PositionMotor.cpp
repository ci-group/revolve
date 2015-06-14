#include "PositionMotor.h"
#include <iostream>
#include <gazebo/math/Rand.hh>

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

	// If the joint has no set limits, these may be very small or large,
	// causing the controller to flip (because it is trying to compensate
	// for a value that's in the order of 1e16 off). Because a joint is never
	// more than a circle we can truncate to a range of size 2PI.
	if (upperLimit_ - lowerLimit_ > (2 * M_PI)) {
		lowerLimit_ = -M_PI;
		upperLimit_ = M_PI;
	}

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
	double output = outputs[0];

	// Motor noise in range +/- noiseLevel * actualValue
	output += ((2 * gz::math::Rand::GetDblUniform() * noise_) -
					  noise_) * output;

	// Truncate output to [0, 1]
	output = fmin(fmax(0, output), 1);

	double position = lowerLimit_ + output * (upperLimit_ - lowerLimit_);
	jointController_->SetPositionTarget(jointName_, position);
}

} /* namespace gazebo */
} /* namespace revolve */
