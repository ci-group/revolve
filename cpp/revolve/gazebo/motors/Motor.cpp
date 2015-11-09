/*
 * Motor.cpp
 *
 *  Created on: Mar 5, 2015
 *      Author: elte
 */

#include <revolve/gazebo/motors/Motor.h>

namespace gz = gazebo;

namespace revolve {
namespace gazebo {

Motor::Motor(::gazebo::physics::ModelPtr model, std::string partId, std::string motorId, unsigned int outputNeurons):
	model_(model),
	partId_(partId),
	motorId_(motorId),
	outputs_(outputNeurons)
{}

Motor::~Motor() {}

std::string Motor::partId() {
	return partId_;
}

unsigned int Motor::outputs() {
	return outputs_;
}

gz::common::PID Motor::createPid(sdf::ElementPtr pidElem) {
	double pv = 0, iv = 0, dv = 0, iMax = 0, iMin = 0,
			cmdMax = 0, cmdMin = 0;

	if (pidElem->HasElement("rv:p")) pv = pidElem->GetElement("rv:p")->Get<double>();
	if (pidElem->HasElement("rv:i")) iv = pidElem->GetElement("rv:i")->Get<double>();
	if (pidElem->HasElement("rv:d")) dv = pidElem->GetElement("rv:d")->Get<double>();
	if (pidElem->HasElement("rv:i_max")) iMax = pidElem->GetElement("rv:i_max")->Get<double>();
	if (pidElem->HasElement("rv:i_min")) iMin = pidElem->GetElement("rv:i_min")->Get<double>();
	if (pidElem->HasElement("rv:cmd_max")) cmdMax = pidElem->GetElement("rv:cmd_max")->Get<double>();
	if (pidElem->HasElement("rv:cmd_min")) cmdMin = pidElem->GetElement("rv:cmd_min")->Get<double>();

	return gz::common::PID(pv, iv, dv, iMax, iMin, cmdMax, cmdMin);
}

std::string Motor::motorId() {
	return motorId_;
}

} /* namespace gazebo */
} /* namespace revolve */
