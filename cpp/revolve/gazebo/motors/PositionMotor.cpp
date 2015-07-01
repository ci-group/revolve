#include "PositionMotor.h"
#include <iostream>
#include <gazebo/math/Rand.hh>

namespace gz = gazebo;

namespace revolve {
namespace gazebo {

PositionMotor::PositionMotor(gz::physics::ModelPtr model, std::string partId,
							 std::string motorId, sdf::ElementPtr motor):
	JointMotor(model, partId, motorId, motor, 1),
	positionTarget_(0),
	noise_(0) {
	// Retrieve upper / lower limit from joint set in parent constructor
	// Truncate ranges to [-pi, pi]
	upperLimit_ = fmin(M_PI, joint_->GetUpperLimit(0).Radian());
	lowerLimit_ = fmax(-M_PI, joint_->GetLowerLimit(0).Radian());
	fullRange_ = (upperLimit_ - lowerLimit_ + 1e-12) >= (2 * M_PI);

	if (motor->HasElement("rv:pid")) {
		auto pidElem = motor->GetElement("rv:pid");
		pid_ = Motor::createPid(pidElem);
	}

	auto noiseParam = motor->GetAttribute("noise");
	if (noiseParam) {
		noiseParam->Get(noise_);
	}

	updateConnection_ = gz::event::Events::ConnectWorldUpdateBegin(boost::bind(
			&PositionMotor::OnUpdate, this, _1));
}

PositionMotor::~PositionMotor() { }

void PositionMotor::OnUpdate(const ::gazebo::common::UpdateInfo info) {
	gz::common::Time stepTime = info.simTime - prevUpdateTime_;

	if (stepTime <= 0) {
		// Only respond to positive step times
		return;
	}

	prevUpdateTime_ = info.simTime;
	auto positionAngle = joint_->GetAngle(0);
	positionAngle.Normalize();
	double position = positionAngle.Radian();

	if (fullRange_ && fabs(position - positionTarget_) > M_PI) {
		// Both the position and the position target will be in the range [-pi, pi]
		// For a full range of motion joint, using an angle +- 2 PI might result
		// in a much shorter required movement. In this case we best correct the
		// current position to something outside the range.
		position += (position > 0 ? -2 * M_PI : 2 * M_PI);
	}

	double cmd = pid_.Update(position - positionTarget_, stepTime);
	joint_->SetForce(0, cmd);
}

void PositionMotor::update(double *outputs, double /*step*/) {
	// Just one network output, which is the first
	double output = outputs[0];

	// Motor noise in range +/- noiseLevel * actualValue
	output += ((2 * gz::math::Rand::GetDblUniform() * noise_) -
					  noise_) * output;

	// Truncate output to [0, 1]
	output = fmin(fmax(0, output), 1);
	positionTarget_ = lowerLimit_ + output * (upperLimit_ - lowerLimit_);
}

} /* namespace gazebo */
} /* namespace revolve */
