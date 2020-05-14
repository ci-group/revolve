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
    , robotStatesPubFreq_(5)
    , lastRobotStatesUpdateTime_(0)
{
}

void unsubscribe(gz::transport::SubscriberPtr &subscription)
{
  if (subscription)
    subscription->Unsubscribe();
}

void fini(gz::transport::PublisherPtr &publisher)
{
  if (publisher)
    publisher->Fini();
}

/////////////////////////////////////////////////
RobotController::~RobotController()
{
  this->node_.reset();
  this->world_.reset();
  this->motorFactory_.reset();
  this->sensorFactory_.reset();

  unsubscribe(this->requestSub_);

  this->lastRobotStatesUpdateTime_ = 0; //this->world_->SimTime().Double();

  fini(this->robotStatesPub_);
}

/////////////////////////////////////////////////
void RobotController::Load(
    ::gazebo::physics::ModelPtr _parent,
    sdf::ElementPtr _sdf)
{
    try {
        // Store the pointer to the model / world
        this->model_ = _parent;
        this->world_ = _parent->GetWorld();
        this->initTime_ = this->world_->SimTime().Double();

        // Create transport node
        this->node_.reset(new gz::transport::Node());
        this->node_->Init();

        // Subscribe to insert request messages
        this->requestSub_ = this->node_->Subscribe(
                "~/request",
                &RobotController::HandleRequest,
                this);

        // Publisher for inserted models
        this->responsePub_ = this->node_->Advertise< gz::msgs::Response >(
              "~/response");

        // Subscribe to robot battery state updater
        this->batterySetSub_ = this->node_->Subscribe(
                "~/battery_level/request",
                &RobotController::UpdateBattery,
                this);
        this->batterySetPub_ = this->node_->Advertise<gz::msgs::Response>(
                "~/battery_level/response");

        // Bind to the world update event to perform some logic
        this->onBeginUpdateConnection = gz::event::Events::ConnectWorldUpdateBegin(
              [this] (const ::gazebo::common::UpdateInfo &_info) {this->OnBeginUpdate(_info);});

        // Robot pose publisher
        this->robotStatesPub_ = this->node_->Advertise< revolve::msgs::RobotStates >(
              "~/revolve/robot_states", 500);

        if (not _sdf->HasElement("rv:robot_config")) {
            std::cerr
                    << "No `rv:robot_config` element found, controller not initialized."
                    << std::endl;
            return;
        }

        auto robotConfiguration = _sdf->GetElement("rv:robot_config");

        if (robotConfiguration->HasElement("rv:update_rate")) {
            auto updateRate = robotConfiguration->GetElement("rv:update_rate")->Get<double>();
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
    catch (const std::exception &e)
    {
        std::cerr << "Error Loading the Robot Controller, expcetion: " << std::endl
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

  /*
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
  */

  batterySetPub_->Publish(resp);
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
    if (not motors_.empty()) {
        brain_.reset(new RLPower(this->model_, brain_sdf, motors_, sensors_));
    }
  }
  else if ("bo" == learner and "cpg" == controller_type)
  {
    brain_.reset(new DifferentialCPG(this->model_, _sdf, motors_, sensors_, this->battery_));
  }
  else if ("offline" == learner and "cpg" == controller_type)
  {
      brain_.reset(new DifferentialCPGClean(brain_sdf, motors_));
  }
  else if ("offline" == learner and "cppn-cpg" == controller_type)
  {
      brain_.reset(new DifferentialCPPNCPG(brain_sdf, motors_));
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

  if (brain_)
    brain_->Update(motors_, sensors_, currentTime, actuationTime_);

  if(battery_)
    battery_->Update(currentTime, actuationTime_);
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

/////////////////////////////////////////////////
void RobotController::OnBeginUpdate(const ::gazebo::common::UpdateInfo &_info) {

  if (not this->robotStatesPubFreq_) {
    return;
  }

  auto secs = 1.0 / this->robotStatesPubFreq_;
  auto time = _info.simTime.Double();
  if ((time - this->lastRobotStatesUpdateTime_) >= secs) {
    // Send robot info update message, this only sends the
    // main pose of the robot (which is all we need for now)
    msgs::RobotStates msg;
    gz::msgs::Set(msg.mutable_time(), _info.simTime);

    {
      boost::recursive_mutex::scoped_lock lock_physics(*this->world_->Physics()->GetPhysicsUpdateMutex());
      for (const auto &model : this->world_->Models()) {
        if (model->IsStatic()) {
          // Ignore static models such as the ground and obstacles
          continue;
        }

        revolve::msgs::RobotState *stateMsg = msg.add_robot_state();
        const std::string scoped_name = model->GetScopedName();
        stateMsg->set_name(scoped_name);
        stateMsg->set_id(model->GetId());

        auto poseMsg = stateMsg->mutable_pose();
        auto relativePose = model->RelativePose();

        gz::msgs::Set(poseMsg, relativePose);

        // Death sentence check
        const std::string name = model->GetName();
        bool death_sentence = false;
        double death_sentence_value = 0;
        {
          boost::mutex::scoped_lock lock_death(death_sentences_mutex_);
          death_sentence = death_sentences_.count(name) > 0;
          if (death_sentence)
            death_sentence_value = death_sentences_[name];
        }

        if (death_sentence) {
          if (death_sentence_value < 0) {
            // Initialize death sentence
            death_sentences_[name] = time - death_sentence_value;
            stateMsg->set_dead(false);
          } else {
            bool alive = death_sentence_value > time;
            stateMsg->set_dead(not alive);

            if (not alive) {
              boost::mutex::scoped_lock lock(this->death_sentences_mutex_);
              this->death_sentences_.erase(model->GetName());

              this->models_to_remove.emplace_back(model);
            }
          }
        }

        if (this->battery_) {
          stateMsg->set_battery_charge(this->battery_->current_charge);
        }
      }
    }

    if (msg.robot_state_size() > 0) {
      this->robotStatesPub_->Publish(msg);
      this->lastRobotStatesUpdateTime_ = time;
    }
  }


//    if (world_insert_remove_mutex.try_lock()) {
  for (const auto &model: this->models_to_remove) {
    std::cout << "Removing " << model->GetScopedName() << std::endl;
//            this->world_->RemoveModel(model);
//            gz::msgs::Request deleteReq;
//            auto id = gz::physics::getUniqueId();
//            deleteReq.set_id(id);
//            deleteReq.set_request("entity_delete");
//            deleteReq.set_data(model->GetScopedName());
//            this->requestPub_->Publish(deleteReq);
    gz::transport::requestNoReply(this->world_->Name(), "entity_delete", model->GetScopedName());
    std::cout << "Removed " << model->GetScopedName() << std::endl;

  }
  this->models_to_remove.clear();
//        this->world_insert_remove_mutex.unlock();
//    }
}

/////////////////////////////////////////////////
// Process insert and delete requests
void RobotController::HandleRequest(ConstRequestPtr &request) {
  std::cout << "RobotController handle request " << std::endl;
  if (request->request() == "insert_sdf")
  {
    std::cout << "Processing insert model request ID `" << request->id() << "`."
              << std::endl;
    sdf::SDF robotSDF;
    robotSDF.SetFromString(request->data());
    double lifespan_timeout = request->dbl_data();

    // Get the model name, store in the expected map
    auto name = robotSDF.Root()->GetElement("model")->GetAttribute("name")
            ->GetAsString();

    if (lifespan_timeout > 0)
    {
      boost::mutex::scoped_lock lock(death_sentences_mutex_);
      // Initializes the death sentence negative because I don't dare to take the
      // simulation time from this thread.
      death_sentences_[name] = -lifespan_timeout;
    }
    //TODO insert here, it's better
    //this->world_->InsertModelString(robotSDF.ToString());

    // Don't leak memory
    // https://bitbucket.org/osrf/sdformat/issues/104/memory-leak-in-element
    robotSDF.Root()->Reset();
  }
  else if (request->request() == "set_robot_state_update_frequency")
  {
    auto frequency = request->data();
    assert(frequency.find_first_not_of( "0123456789" ) == std::string::npos);
    this->robotStatesPubFreq_ = (unsigned int)std::stoul(frequency);
    std::cout << "Setting robot state update frequency to "
              << this->robotStatesPubFreq_ << "." << std::endl;

    gz::msgs::Response resp;
    resp.set_id(request->id());
    resp.set_request("set_robot_state_update_frequency");
    resp.set_response("success");

    this->responsePub_->Publish(resp);
  }
}