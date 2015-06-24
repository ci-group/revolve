#include "VelocityMotor.h"

namespace gz = gazebo;

namespace revolve {
namespace gazebo {


VelocityMotor::VelocityMotor(::gazebo::physics::ModelPtr model, std::string partId,
                             std::string motorId, sdf::ElementPtr motor):
    JointMotor(model, partId, motorId, motor, 1),
    noise_(0)
{
	if (motor->HasElement("rv:pid")) {
		auto pidElem = motor->GetElement("rv:pid");
		pid_ = Motor::createPid(pidElem);
	}

    if (!motor->HasAttribute("min_velocity") || !motor->HasAttribute("max_velocity")) {
        std::cerr << "Missing servo min/max velocity parameters, "
                "velocity will be zero." << std::endl;
        minVelocity_ = maxVelocity_ = 0;
    } else {
        motor->GetAttribute("min_velocity")->Get(minVelocity_);
        motor->GetAttribute("max_velocity")->Get(maxVelocity_);
    }

    joint_->SetVelocityLimit(0, fmax(fabs(minVelocity_), fabs(maxVelocity_)));
}

VelocityMotor::~VelocityMotor() {}

void VelocityMotor::update(double * outputs, double step) {
    // Just one network output, which is the first
    double output = outputs[0];

    // Motor noise in range +/- noiseLevel * actualValue
    output += ((2 * gz::math::Rand::GetDblUniform() * noise_) -
                      noise_) * output;

	// Truncate output to [0, 1]
	output = fmax(fmin(output, 1), 0);

    double velocityTarget = minVelocity_ + output * (maxVelocity_ - minVelocity_);
    double currentVelocity = joint_->GetVelocity(0);
    gz::common::Time dt(step);
    double cmd = pid_.Update(currentVelocity - velocityTarget, dt);
    joint_->SetForce(0, cmd);
}

} // namespace gazebo
} // namespace revolve


