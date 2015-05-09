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

Motor::Motor(::gazebo::physics::ModelPtr model, std::string partId, unsigned int outputNeurons):
	model_(model),
	outputs_(outputNeurons),
	partId_(partId)
{}

Motor::~Motor() {}

std::string Motor::partId() {
	return partId_;
}

unsigned int Motor::outputs() {
	return outputs_;
}

gz::common::PID Motor::createPid(sdf::ElementPtr pidElem) {
	auto pParam = pidElem->GetAttribute("p");
	auto iParam = pidElem->GetAttribute("i");
	auto dParam = pidElem->GetAttribute("d");
	auto iMaxParam = pidElem->GetAttribute("i_max");
	auto iMinParam = pidElem->GetAttribute("i_min");
	auto cmdMaxParam = pidElem->GetAttribute("cmd_max");
	auto cmdMinParam = pidElem->GetAttribute("cmd_min");

	double pv = 0, iv = 0, dv = 0, iMax = 0, iMin = 0,
			cmdMax = 0, cmdMin = 0;

	if (pParam) pParam->Get(pv);
	if (iParam) iParam->Get(iv);
	if (dParam) dParam->Get(dv);
	if (iMaxParam) iMaxParam->Get(iMax);
	if (iMinParam) iMinParam->Get(iMin);
	if (cmdMaxParam) cmdMaxParam->Get(cmdMax);
	if (cmdMinParam) cmdMinParam->Get(cmdMin);

	return gz::common::PID(pv, iv, dv, iMax, iMin, cmdMax, cmdMin);
}

} /* namespace gazebo */
} /* namespace revolve */
