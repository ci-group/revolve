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

#include <stdexcept>

#include <gazebo/sensors/sensors.hh>

#include <revolve/gazebo/motors/MotorFactory.h>
#include <revolve/gazebo/sensors/SensorFactory.h>
#include <revolve/gazebo/sensors/GZAngleToTargetDetector.h>
#include <revolve/gazebo/brains/Brains.h>
#include <revolve/gazebo/brains/FixedAngleController.h>

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
  try
  {
    // Store the pointer to the model / world
    this->model_ = _parent;
    this->world_ = _parent->GetWorld();
    this->initTime_ = this->world_->SimTime().Double();

    // Create transport node
    this->node_.reset(new gz::transport::Node());
    this->node_->Init();

    // Subscribe to robot battery state updater
    this->batterySetSub_ = this->node_->Subscribe(
        "~/battery_level/request",
        &RobotController::UpdateBattery,
        this);
    this->batterySetPub_ = this->node_->Advertise<gz::msgs::Response>(
        "~/battery_level/response");

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
      auto updateRate = robotConfiguration->GetElement("rv:update_rate")->Get<double>();
      this->actuationTime_ = 1.0 / updateRate;
    }

    // Load motors
    this->motorFactory_ = this->MotorFactory(_parent);
    this->LoadActuators(robotConfiguration);

    // Load sensors
    this->sensorFactory_ = this->SensorFactory(_parent);
    this->LoadSensors(robotConfiguration);

    // Load brain, this needs to be done after the motors and sensors so they
    // can potentially be reordered.
    this->LoadBrain(robotConfiguration);

    // Call the battery loader
    this->LoadBattery(robotConfiguration);

    // Call startup function which decides on actuation
    this->Startup(_parent, _sdf);
  }
  catch (const std::exception &e)
  {
    std::cerr << "Error Loading the Robot Controller, exception: " << std::endl
              << e.what() << std::endl;
    throw;
  }
}

/////////////////////////////////////////////////
void RobotController::UpdateBattery(ConstRequestPtr &_request)
{
  if (_request->data() not_eq this->model_->GetName() and
      _request->data() not_eq this->model_->GetScopedName())
  {
    return;
  }

  gz::msgs::Response resp;
  resp.set_id(_request->id());
  resp.set_request(_request->request());

  if (_request->request() == "set_battery_level")
  {
    resp.set_response("success");
    this->SetBatteryLevel(_request->dbl_data());
  }
  else
  {
    std::stringstream ss;
    ss << this->BatteryLevel();
    resp.set_response(ss.str());
  }

  batterySetPub_->Publish(resp);
}

/////////////////////////////////////////////////
void RobotController::LoadActuators(const sdf::ElementPtr _sdf)
{
  if (not _sdf->HasElement("rv:brain") or not _sdf->GetElement("rv:brain")->HasElement("rv:actuators"))
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
      auto servomotorObj = this->motorFactory_->Create(servomotor);
      motors_.push_back(servomotorObj);
      servomotor = servomotor->GetNextElement("rv:servomotor");
    }
  }
}

/////////////////////////////////////////////////
void RobotController::LoadSensors(const sdf::ElementPtr _sdf)
{
  if (not _sdf->HasElement("rv:brain") or not _sdf->GetElement("rv:brain")->HasElement("rv:sensors"))
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

  auto brain_sdf = _sdf->GetElement("rv:brain");
  auto controller_type = brain_sdf->GetElement("rv:controller")->GetAttribute("type")->GetAsString();
  auto learner = brain_sdf->GetElement("rv:learner")->GetAttribute("type")->GetAsString();
  std::cout << "Loading controller " << controller_type << " and learner " << learner << std::endl;

  if ("offline" == learner and "ann" == controller_type)
  {
    brain_.reset(new NeuralNetwork(this->model_, brain_sdf, motors_, sensors_));
  }
  else if ("rlpower" == learner and "spline" == controller_type)
  {
    if (not motors_.empty())
    {
      brain_.reset(new RLPower(this->model_, brain_sdf, motors_, sensors_));
    }
  }
  else if ("bo" == learner and "cpg" == controller_type)
  {
    //WARNING! not doing BO any more
    brain_.reset(new DifferentialCPG(_sdf, motors_));
  }
  else if ("target" == learner and "cpg" == controller_type)
  {
    std::shared_ptr<revolve::AngleToTargetDetector> fake_target_sensor(
        new GZAngleToTargetDetector(this->model_, ignition::math::Vector3d(0, 10, 0)));
    brain_.reset(new DifferentialCPGClean(brain_sdf, motors_, fake_target_sensor));
  }
  else if ("offline" == learner && "cpg-target" == controller_type)
  {
    std::vector<double> target_vec;
    std::string target_str = brain_sdf->GetElement("rv:controller")->GetAttribute("target")->GetAsString();
    std::string delimiter = ";";
    size_t pos = 0;
    std::string token;
    std::cout << "The generated target equals (" << target_str << ")" << std::endl;
    while ((pos = target_str.find(delimiter)) != std::string::npos)
    {
      token = target_str.substr(0, pos);
      target_vec.push_back(stod(token));
      target_str.erase(0, pos + delimiter.length());
    }
    // push the last element that does not end with the delimiter
    target_vec.push_back(stod(target_str));

    ignition::math::Vector3d target(target_vec[0], target_vec[1], target_vec[2]);

    std::shared_ptr<revolve::AngleToTargetDetector> fake_target_sensor(
        new GZAngleToTargetDetector(this->model_, target));
    brain_.reset(new DifferentialCPGClean(brain_sdf, motors_, fake_target_sensor));
  }
  else if ("offline" == learner and "cpg" == controller_type)
  {
    brain_.reset(new DifferentialCPGClean(brain_sdf, motors_));
  }
  else if ("offline" == learner and "cppn-cpg" == controller_type)
  {
    brain_.reset(new DifferentialCPPNCPG(brain_sdf, motors_));
  }
  else if ("offline" == learner and "fixed-angle" == controller_type)
  {
    double angle = std::stod(
        brain_sdf->GetElement("rv:controller")->GetAttribute("angle")->GetAsString());
    brain_.reset(new FixedAngleController(angle));
  }
  else
  {
    std::ostringstream message;
    message << "Robot brain is not defined. (learner='" << learner << "', controller='" << controller_type << "')";
    throw std::runtime_error(message.str());
  }
  std::cout << "Loaded controller " << controller_type << " and learner " << learner << std::endl;
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
  auto currentTime = _info.simTime.Double() - initTime_;

  if (brain_)
    brain_->update(motors_, sensors_, currentTime, actuationTime_);
}

/////////////////////////////////////////////////
void RobotController::LoadBattery(const sdf::ElementPtr _sdf)
{
  if (_sdf->HasElement("rv:battery"))
  {
    this->batteryElem_ = _sdf->GetElement("rv:battery");
  }
}

/////////////////////////////////////////////////
double RobotController::BatteryLevel()
{
  if (not batteryElem_ or not batteryElem_->HasElement("rv:level"))
  {
    return 0.0;
  }

  return batteryElem_->GetElement("rv:level")->Get<double>();
}

/////////////////////////////////////////////////
void RobotController::SetBatteryLevel(double _level)
{
  if (batteryElem_ and batteryElem_->HasElement("rv:level"))
  {
    batteryElem_->GetElement("rv:level")->Set(_level);
  }
}
