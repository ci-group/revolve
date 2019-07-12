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
* Date: June 6, 2015
*
*/

#include <string>

#include "WorldController.h"

namespace gz = gazebo;

using namespace revolve::gazebo;

/////////////////////////////////////////////////
WorldController::WorldController()
    : delete_robot_queue()
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

WorldController::~WorldController()
{
    unsubscribe(this->requestSub_);
    unsubscribe(this->responseSub_);
    unsubscribe(this->modelSub_);
    fini(this->requestPub_);
    fini(this->responsePub_);
    fini(this->robotStatesPub_);
}

/////////////////////////////////////////////////
void WorldController::Load(
    gz::physics::WorldPtr world,
    sdf::ElementPtr /*_sdf*/)
{
  std::cout << "World plugin loaded." << std::endl;

  // Store the world
  this->world_ = world;

  // Create transport node
  this->node_.reset(new gz::transport::Node());
  this->node_->Init();

  // Subscribe to insert request messages
  this->requestSub_ = this->node_->Subscribe(
      "~/request",
      &WorldController::HandleRequest,
      this);

  // Publisher for `entity_delete` requests.
  this->requestPub_ = this->node_->Advertise< gz::msgs::Request >(
      "~/request");

  // Publisher for inserted models
  this->responseSub_ = this->node_->Subscribe(
      "~/response",
      &WorldController::HandleResponse,
      this);

  // Publisher for inserted models
  this->responsePub_ = this->node_->Advertise< gz::msgs::Response >(
      "~/response");

  // Since models are added asynchronously, we need some way of detecting
  // our model add. We do this using a model info subscriber.
  this->modelSub_ = this->node_->Subscribe(
      "~/model/info",
      &WorldController::OnModel,
      this);

  // Bind to the world update event to perform some logic
  this->onBeginUpdateConnection = gz::event::Events::ConnectWorldUpdateBegin(
      [this] (const ::gazebo::common::UpdateInfo &_info) {this->OnBeginUpdate(_info);});

  // Bind to the world update event to perform some logic
  this->onEndUpdateConnection = gz::event::Events::ConnectWorldUpdateEnd(
        [this] () {this->OnEndUpdate();});

  // Robot pose publisher
  this->robotStatesPub_ = this->node_->Advertise< revolve::msgs::RobotStates >(
      "~/revolve/robot_states", 500);
}

void WorldController::Reset()
{
    this->lastRobotStatesUpdateTime_ = 0; //this->world_->SimTime().Double();
}

/////////////////////////////////////////////////
void WorldController::OnBeginUpdate(const ::gazebo::common::UpdateInfo &_info) {
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
            boost::mutex::scoped_lock lock_death(death_sentences_mutex_);
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
                if (death_sentences_.count(name) > 0) {
                    double death_sentence = death_sentences_[name];
                    if (death_sentence < 0) {
                        // Initialize death sentence
                        death_sentences_[name] = time - death_sentence;
                    } else {
                        bool alive = death_sentence > time;
                        stateMsg->set_dead(not alive);

                        if (not alive)
                            model->Fini();
                    }
                }
            }
        }

        if (msg.robot_state_size() > 0) {
            this->robotStatesPub_->Publish(msg);
            this->lastRobotStatesUpdateTime_ = time;
        }
    }
}

void WorldController::OnEndUpdate()
{
    { // check if there are robots to delete
        std::tuple< ::gazebo::physics::ModelPtr, int> delete_robot;
        {
            boost::mutex::scoped_lock lock(this->deleteMutex_);
            if (not this->delete_robot_queue.empty()) {
                delete_robot = this->delete_robot_queue.front();
                this->delete_robot_queue.pop();
            }
        }
        auto model = std::get<0>(delete_robot);
        auto request_id = std::get<1>(delete_robot);
        if (model) {
//            this->world_->SetPaused(true);
            this->world_->RemoveModel(model);
//            this->world_->SetPaused(true);

            gz::msgs::Response resp;
            resp.set_id(request_id);
            resp.set_request("delete_robot");
            resp.set_response("success");
            this->responsePub_->Publish(resp);
        }
    }
}


/////////////////////////////////////////////////
// Process insert and delete requests
void WorldController::HandleRequest(ConstRequestPtr &request)
{
  if (request->request() == "delete_robot")
  {
    auto name = request->data();
    std::cout << "Processing request `" << request->id()
              << "` to delete robot `" << name << "`" << std::endl;

    auto model = this->world_->ModelByName(name);
    if (model)
    {
      // Tell the world to remove the model
      // Using `World::RemoveModel()` from here crashes the transport
      // library, the cause of which I've yet to figure out - it has
      // something to do with race conditions where the model is used by
      // the world while it is being updated. Fixing this completely
      // appears to be a rather involved process, instead, we'll use an
      // `entity_delete` request, which will make sure deleting the model
      // happens on the world thread.
      gz::msgs::Request deleteReq;
      auto id = gz::physics::getUniqueId();
      deleteReq.set_id(id);
      deleteReq.set_request("entity_delete");
      deleteReq.set_data(model->GetScopedName());

      {
        boost::mutex::scoped_lock lock(this->deleteMutex_);
        this->delete_robot_queue.emplace(std::make_tuple(model, request->id()));
      }
      {
        boost::mutex::scoped_lock lock(this->death_sentences_mutex_);
        this->death_sentences_.erase(model->GetName());
      }

      this->requestPub_->Publish(deleteReq);
    }
    else
    {
      std::cerr << "Model `" << name << "` could not be found in the world."
                << std::endl;
      gz::msgs::Response resp;
      resp.set_id(request->id());
      resp.set_request("delete_robot");
      resp.set_response("error");
      this->responsePub_->Publish(resp);
    }
  }
  else if (request->request() == "insert_sdf")
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

    {
      boost::mutex::scoped_lock lock(this->insertMutex_);
      this->insertMap_[name] = request->id();
    }

//    this->world_->SetPaused(true);
    this->world_->InsertModelString(robotSDF.ToString());
//    this->world_->SetPaused(false);

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

/////////////////////////////////////////////////
void WorldController::OnModel(ConstModelPtr &msg)
{
  auto name = msg->name();

  int id;
  {
    boost::mutex::scoped_lock lock(this->insertMutex_);
    if (this->insertMap_.count(name) <= 0)
    {
      // Insert was not requested here, ignore it
      return;
    }
    id = this->insertMap_[name];
    this->insertMap_.erase(name);
  }

  // Respond with the inserted model
  gz::msgs::Response resp;
  resp.set_request("insert_sdf");
  resp.set_response("success");
  resp.set_id(id);

  msgs::ModelInserted inserted;
  inserted.mutable_model()->CopyFrom(*msg);
  gz::msgs::Set(inserted.mutable_time(), this->world_->SimTime());
  inserted.SerializeToString(resp.mutable_serialized_data());

  this->responsePub_->Publish(resp);

  std::cout << "Model `" << name << "` inserted, world now contains "
            << this->world_->ModelCount() << " models." << std::endl;
}

/////////////////////////////////////////////////
void WorldController::HandleResponse(ConstResponsePtr &response)
{
}
