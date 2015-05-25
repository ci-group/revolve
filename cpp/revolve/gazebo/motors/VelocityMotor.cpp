//
// Created by elte on 17-5-15.
//

#include <revolve/gazebo/motors/VelocityMotor.h>

namespace gz = gazebo;

namespace revolve {
namespace gazebo {


VelocityMotor::VelocityMotor(::gazebo::physics::ModelPtr model, std::string partId,
                             std::string motorId, sdf::ElementPtr motor):
    JointMotor(model, partId, motorId, motor, 1),
    jointController_(model->GetJointController()),
    noise_(0)
{
	if (motor->HasElement("rv:pid")) {
		auto pidElem = motor->GetElement("rv:pid");
		auto pid = Motor::createPid(pidElem);
		jointController_->SetVelocityPID(jointName_, pid);
	}

    if (!motor->HasAttribute("min_velocity") || !motor->HasAttribute("max_velocity")) {
        std::cerr << "Missing servo min/max velocity parameters, "
                "velocity will be zero." << std::endl;
    } else {
        motor->GetAttribute("min_velocity")->Get(minVelocity_);
        motor->GetAttribute("max_velocity")->Get(maxVelocity_);
    }
}

VelocityMotor::~VelocityMotor() {}

void VelocityMotor::update(double * outputs, unsigned int /*step*/) {
    // Just one network output, which is the first
    double output = outputs[0];

	std::cout << output << std::endl;

    // Motor noise in range +/- noiseLevel * actualValue
    output += ((2 * gz::math::Rand::GetDblUniform() * noise_) -
                      noise_) * output;

    double velocity = minVelocity_ + output * (maxVelocity_ - minVelocity_);
    jointController_->SetVelocityTarget(jointName_, velocity);
}

} // namespace gazebo
} // namespace revolve


