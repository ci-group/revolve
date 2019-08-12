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
* Date: May 3, 2015
*
*/

#include  <stdexcept>

#include <gazebo/sensors/sensors.hh>

#include <revolve/gazebo/motors/MotorFactory.h>
#include <revolve/gazebo/sensors/SensorFactory.h>
#include <revolve/gazebo/brains/Brains.h>
#include <revolve/gazebo/battery/Battery.h>

#include "RobotController.h"

namespace gz = gazebo;

using namespace revolve::gazebo;

/////////////////////////////////////////////////
/// Default actuation time is given and this will be overwritten by the plugin
/// config in Load.
RobotController::RobotController()
    : actuationTime_(0)
{
}

/////////////////////////////////////////////////
RobotController::~RobotController()
{
  this->node_.reset();
  this->world_.reset();
  this->motorFactory_.reset();
  this->sensorFactory_.reset();
}

/////////////////////////////////////////////////
void RobotController::Load(
    ::gazebo::physics::ModelPtr _parent,
    sdf::ElementPtr _sdf)
{
  // Store the pointer to the model / world
  this->model_ = _parent;
  this->world_ = _parent->GetWorld();
  this->initTime_ = this->world_->SimTime().Double();

  // Create transport node
  this->node_.reset(new gz::transport::Node());
  this->node_->Init();


  if (not _sdf->HasElement("rv:robot_config"))
  {
    std::cerr
        << "No `rv:robot_config` element found, controller not initialized."
        << std::endl;
    return;
  }

  auto robotConfiguration = _sdf->GetElement("rv:robot_config");

  if (robotConfiguration->HasElement("rv:update_rate"))
  {
    auto updateRate = robotConfiguration->GetElement("rv:update_rate")->Get< double >();
    this->actuationTime_ = 1.0 / updateRate;
  }

  // Call the battery loader
  this->LoadBattery(robotConfiguration);

  // Load motors
  this->motorFactory_ = this->MotorFactory(_parent);
  this->LoadActuators(robotConfiguration);

  // Load sensors
  this->sensorFactory_ = this->SensorFactory(_parent);
  this->LoadSensors(robotConfiguration);

  // Load brain, this needs to be done after the motors and sensors so they
  // can potentially be reordered.
  this->LoadBrain(robotConfiguration);

  // Call startup function which decides on actuation
  this->Startup(_parent, _sdf);
}

/////////////////////////////////////////////////
void RobotController::LoadActuators(const sdf::ElementPtr _sdf)
{
  if (not _sdf->HasElement("rv:brain")
      or not _sdf->GetElement("rv:brain")->HasElement("rv:actuators"))
  {
    return;
  }
  auto actuators = _sdf->GetElement("rv:brain")->GetElement("rv:actuators");

  // Load actuators of type servomotor
  if (actuators->HasElement("rv:servomotor"))
  {
    auto servomotor = actuators->GetElement("rv:servomotor");
    while (servomotor)
    {
      auto servomotorObj = this->motorFactory_->Create(servomotor, this->battery_);
      motors_.push_back(servomotorObj);
      servomotor = servomotor->GetNextElement("rv:servomotor");
    }
  }
}

/////////////////////////////////////////////////
void RobotController::LoadSensors(const sdf::ElementPtr _sdf)
{
  if (not _sdf->HasElement("rv:brain")
      or not _sdf->GetElement("rv:brain")->HasElement("rv:sensors"))
  {
    return;
  }
  auto sensors = _sdf->GetElement("rv:brain")->GetElement("rv:sensors");

  // Load sensors
  auto sensor = sensors->GetElement("rv:sensor");
  while (sensor)
  {
    auto sensorObj = this->sensorFactory_->Create(sensor);
    sensors_.push_back(sensorObj);
    sensor = sensor->GetNextElement("rv:sensor");
  }
}

/////////////////////////////////////////////////
MotorFactoryPtr RobotController::MotorFactory(
    ::gazebo::physics::ModelPtr _model)
{
  return MotorFactoryPtr(new class MotorFactory(_model));
}

/////////////////////////////////////////////////
SensorFactoryPtr RobotController::SensorFactory(
    ::gazebo::physics::ModelPtr _model)
{
  return SensorFactoryPtr(new class SensorFactory(_model));
}

/////////////////////////////////////////////////
void RobotController::LoadBrain(const sdf::ElementPtr _sdf)
{
  if (not _sdf->HasElement("rv:brain"))
  {
    std::cerr << "No robot brain detected, this is probably an error."
              << std::endl;
    return;
  }

  auto brain = _sdf->GetElement("rv:brain");
  auto controller = brain->GetElement("rv:controller")->GetAttribute("type")->GetAsString();
  auto learner = brain->GetElement("rv:learner")->GetAttribute("type")->GetAsString();
  std::cout << "Loading controller " << controller << " and learner " << learner << std::endl;

  if ("offline" == learner and "ann" == controller)
  {
    brain_.reset(new NeuralNetwork(this->model_, brain, motors_, sensors_));
  }
  else if ("rlpower" == learner and "spline" == controller)
  {
    brain_.reset(new RLPower(this->model_, brain, motors_, sensors_));
  }
  else if ("bo" == learner and "cpg" == controller)
  {
    brain_.reset(new DifferentialCPG(this->model_, _sdf, motors_, sensors_, this->battery_));
  }
  else
  {
    throw std::runtime_error("Robot brain is not defined.");
  }
}

/////////////////////////////////////////////////
/// Default startup, bind to CheckUpdate
void RobotController::Startup(
    ::gazebo::physics::ModelPtr /*_parent*/,
    sdf::ElementPtr /*_sdf*/)
{
  this->updateConnection_ = gz::event::Events::ConnectWorldUpdateBegin(
      boost::bind(&RobotController::CheckUpdate, this, _1));
}

/////////////////////////////////////////////////
void RobotController::CheckUpdate(const ::gazebo::common::UpdateInfo _info)
{
  auto diff = _info.simTime - lastActuationTime_;

  if (diff.Double() > actuationTime_)
  {
    this->DoUpdate(_info);
    lastActuationTime_ = _info.simTime;
  }
}

/////////////////////////////////////////////////
/// Default update function simply tells the brain to perform an update
void RobotController::DoUpdate(const ::gazebo::common::UpdateInfo _info)
{
    ///TODO fix this when you have the right amount of initial charge for robots
//    if (battery_->current_charge < 0)
//    {
//        std::exit(0);
//    }


  auto currentTime = _info.simTime.Double() - initTime_;

  /// exits out of simulation after 30 mins of simulation time
//  if (initTime_ > 30)
//  {
//      std::exit(0);
//  }
  this->brain_->Update(motors_, sensors_, currentTime, actuationTime_);
  this->battery_->Update(currentTime, actuationTime_);
}

/////////////////////////////////////////////////
void RobotController::LoadBattery(const sdf::ElementPtr _sdf)
{
  if (_sdf->HasElement("rv:battery"))
  {
    sdf::ElementPtr batteryElem = _sdf->GetElement("rv:battery");
    double battery_initial_charge;
    try {
        battery_initial_charge = std::stod(
                batteryElem->GetAttribute("initial_charge")->GetAsString()
        );
    } catch(std::invalid_argument &e) {
        std::clog << "Initial charge of the robot not set, using 0.0" << std::endl;
        battery_initial_charge = 0.0;
    }
    this->battery_.reset(new ::revolve::gazebo::Battery(battery_initial_charge)); // set initial battery (joules)
    this->battery_->UpdateParameters(batteryElem);
    this->battery_->ResetVoltage();
    this->battery_->robot_name = this->model_->GetName();

  }
}
