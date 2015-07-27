#include "VelocityMotor.h"

namespace gz = gazebo;

namespace revolve {
namespace gazebo {


VelocityMotor::VelocityMotor(::gazebo::physics::ModelPtr model, std::string partId,
                             std::string motorId, sdf::ElementPtr motor):
    JointMotor(model, partId, motorId, motor, 1),
	velocityTarget_(0),
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

	// I've asked this question at the Gazebo forums:
	// http://answers.gazebosim.org/question/9071/joint-target-velocity-with-maximum-force/
	// Until it is answered I'm resorting to calling ODE functions directly to get this
	// to work. This will result in some deprecation warnings. The update connection
	// is no longer needed though.
	//	updateConnection_ = gz::event::Events::ConnectWorldUpdateBegin(boost::bind(
//			&VelocityMotor::OnUpdate, this, _1));
	double maxEffort = joint_->GetEffortLimit(0);
	joint_->SetParam("fmax", 0, maxEffort);
}

VelocityMotor::~VelocityMotor() {}

//void VelocityMotor::OnUpdate(const ::gazebo::common::UpdateInfo info) {
//	this->DoUpdate(info.simTime);
//}

void VelocityMotor::update(double * outputs, double /*step*/) {
    // Just one network output, which is the first
    double output = outputs[0];

    // Motor noise in range +/- noiseLevel * actualValue
    output += ((2 * gz::math::Rand::GetDblUniform() * noise_) -
                      noise_) * output;

	// Truncate output to [0, 1]
	output = fmax(fmin(output, 1), 0);
    velocityTarget_ = minVelocity_ + output * (maxVelocity_ - minVelocity_);
	DoUpdate(joint_->GetWorld()->GetSimTime());
}

void VelocityMotor::DoUpdate(const ::gazebo::common::Time &simTime) {
	gz::common::Time stepTime = simTime - prevUpdateTime_;

	if (stepTime <= 0) {
		// Only respond to positive step times
		return;
	}

	double currentVelocity = joint_->GetVelocity(0);
	double cmd = pid_.Update(currentVelocity - velocityTarget_, stepTime);

	// I'm caving for now and am setting ODE parameters directly.
	// See http://answers.gazebosim.org/question/9071/joint-target-velocity-with-maximum-force/
	joint_->SetParam("vel", 0, cmd);
}

} // namespace gazebo
} // namespace revolve


