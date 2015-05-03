/*
 * ModelController.cpp
 *
 *  Created on: May 3, 2015
 *      Author: elte
 */

#include <revolve/gazebo/plugin/ModelController.h>

#include <iostream>
#include <stdexcept>

namespace gz = gazebo;

namespace revolve {
namespace gazebo {

ModelController::ModelController():
	// Default actuation time, this will be overwritten
	// by the plugin config in Load.
	actuationTime_(0),
	lastActuationSec_(0),
	lastActuationNsec_(0)
{}

ModelController::~ModelController()
{}

void ModelController::Load(::gazebo::physics::ModelPtr _parent,
		sdf::ElementPtr _sdf) {
	// Store the pointer to the model
	this->model = _parent;
	this->world = _parent->GetWorld();

	std::cout << "Plugin loaded." << std::endl;

	if (!_sdf->HasElement("rv:robot_config")) {
		std::cerr << "No `rv:robot_config` element found, controller not initialized."
			  << std::endl;
		return;
	}

	auto settings = _sdf->GetElement("rv:robot_config");

	// Load motors
	this->loadMotors(settings);

	// Load sensors
	this->loadSensors(settings);

	// Load brain, this needs to be done after the motors and
	// sensors so they can be reordered.
	this->loadBrain(settings);

//	if (!this->driver) {
//		std::cerr << "No driving sensor was found, robot will not be actuated." << std::endl;
//		return;
//	}
}

} /* namespace gazebo */
} /* namespace revolve */
