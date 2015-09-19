/*
 * ModelController.cpp
 *
 *  Created on: May 3, 2015
 *      Author: elte
 */

#include <revolve/gazebo/motors/MotorFactory.h>
#include <revolve/gazebo/sensors/SensorFactory.h>
#include <revolve/gazebo/brain/NeuralNetwork.h>

#include <gazebo/transport/transport.hh>
#include <gazebo/sensors/sensors.hh>

#include <boost/bind.hpp>
#include "RobotController.h"

#include <iostream>
#include <stdexcept>

namespace gz = gazebo;

namespace revolve {
namespace gazebo {

RobotController::RobotController():
	// Default actuation time, this will be overwritten
	// by the plugin config in Load.
	actuationTime_(0)
{}

RobotController::~RobotController()
{}

void RobotController::Load(::gazebo::physics::ModelPtr _parent,
		sdf::ElementPtr _sdf) {
	// Store the pointer to the model
	this->model = _parent;
	this->world = _parent->GetWorld();
	this->initTime = this->world->GetSimTime();

	if (!_sdf->HasElement("rv:robot_config")) {
		std::cerr << "No `rv:robot_config` element found, controller not initialized."
			  << std::endl;
		return;
	}

	auto settings = _sdf->GetElement("rv:robot_config");

	if (settings->HasElement("rv:update_rate")) {
		double updateRate = settings->GetElement("rv:update_rate")->Get< double >();
		actuationTime_ = 1.0 / updateRate;
	}

	// Load motors
	this->motorFactory_ = this->getMotorFactory(_parent);
	this->loadMotors(settings);

	// Load sensors
	this->sensorFactory_ = this->getSensorFactory(_parent);
	this->loadSensors(settings);

	// Load brain, this needs to be done after the motors and
	// sensors so they can potentially be reordered.
	this->loadBrain(settings);

	// Call startup function which decides on actuation
	this->startup(_parent, _sdf);
}

void RobotController::loadMotors(sdf::ElementPtr sdf) {
	if (!sdf->HasElement("rv:motor")) {
		return;
	}

	auto motor = sdf->GetElement("rv:motor");
    while (motor) {
    	auto motorObj = this->motorFactory_->create(motor);
    	motors_.push_back(motorObj);
    	motor = motor->GetNextElement("rv:motor");
    }
}

void RobotController::loadSensors(sdf::ElementPtr sdf) {
	if (!sdf->HasElement("rv:sensor")) {
		return;
	}

	auto sensor = sdf->GetElement("rv:sensor");
	while (sensor) {
		auto sensorObj = this->sensorFactory_->create(sensor);
		sensors_.push_back(sensorObj);
		sensor = sensor->GetNextElement("rv:sensor");
	}
}

MotorFactoryPtr RobotController::getMotorFactory(
		::gazebo::physics::ModelPtr model) {
	return MotorFactoryPtr(new MotorFactory(model));
}

SensorFactoryPtr RobotController::getSensorFactory(
		::gazebo::physics::ModelPtr model) {
	return SensorFactoryPtr(new SensorFactory(model));
}

void RobotController::loadBrain(sdf::ElementPtr sdf) {
	if (!sdf->HasElement("rv:brain")) {
		std::cerr << "No robot brain detected, this is probably an error." << std::endl;
		return;
	}
	auto brain = sdf->GetElement("rv:brain");
	brain_.reset(new NeuralNetwork(brain, motors_, sensors_));
}

// Default startup, bind to CheckUpdate
void RobotController::startup(::gazebo::physics::ModelPtr /*_parent*/, sdf::ElementPtr /*_sdf*/) {
	this->updateConnection_ = gz::event::Events::ConnectWorldUpdateBegin(
		boost::bind(&RobotController::CheckUpdate, this, _1));
}

void RobotController::CheckUpdate(const ::gazebo::common::UpdateInfo info) {
	auto diff = info.simTime - lastActuationTime_;

	if (diff.Double() > actuationTime_) {
		lastActuationTime_ = info.simTime;
		this->DoUpdate(info);
	}
}

// Default update function simply tells the brain to perform an update
void RobotController::DoUpdate(const ::gazebo::common::UpdateInfo info) {
	brain_->update(motors_, sensors_, (info.simTime - this->initTime).Double(), actuationTime_);
}

} /* namespace gazebo */
} /* namespace revolve */
