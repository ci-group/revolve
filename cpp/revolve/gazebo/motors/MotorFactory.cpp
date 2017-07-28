/*
* Copyright (C) 2017 Vrije Universiteit Amsterdam
*
* Licensed under the Apache License, Version 2.0 (the "License");
* You may obtain a copy of the License at
*
*     http://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
*
* Author: Elte Hupkes
* Date: Mar 16, 2015
*
*/

#include <revolve/gazebo/motors/MotorFactory.h>
#include <revolve/gazebo/motors/Motors.h>

#include <cstdlib>

namespace gz = gazebo;

namespace revolve {
namespace gazebo {

MotorFactory::MotorFactory(::gazebo::physics::ModelPtr model):
	model_(model)
{}

MotorFactory::~MotorFactory() {}

MotorPtr MotorFactory::getMotor(sdf::ElementPtr motor, const std::string & type,
								const std::string & partId, const std::string & motorId) {
	MotorPtr motorObj;
	if ("position" == type) {
		motorObj.reset(new PositionMotor(model_, partId, motorId, motor));
	} else if ("velocity" == type) {
		motorObj.reset(new VelocityMotor(model_, partId, motorId, motor));
	}

	return motorObj;
}

MotorPtr MotorFactory::create(sdf::ElementPtr motor) {
	auto typeParam = motor->GetAttribute("type");
	auto partIdParam = motor->GetAttribute("part_id");
	auto idParam = motor->GetAttribute("id");

	if (!typeParam || !partIdParam || !idParam) {
		std::cerr << "Motor is missing required attributes (`id`, `type` or `part_id`)." << std::endl;
		throw std::runtime_error("Motor error");
	}

	auto partId = partIdParam->GetAsString();
	auto type = typeParam->GetAsString();
	auto id = idParam->GetAsString();
	MotorPtr motorObj = this->getMotor(motor, type, partId, id);

	if (!motorObj) {
		std::cerr << "Motor type '" << type <<
				"' is unknown." << std::endl;
		throw std::runtime_error("Motor error");
	}

	return motorObj;
}

} /* namespace gazebo */
} /* namespace revolve */
