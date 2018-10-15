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

#include "WorldController.h"

namespace gz = gazebo;

using namespace revolve::gazebo;

/////////////////////////////////////////////////
WorldController::WorldController()
    : robotStatesPubFreq_(0)
    , lastRobotStatesUpdateTime_(0)
{
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
  this->updateConnection_ = gz::event::Events::ConnectWorldUpdateBegin(
      boost::bind(&WorldController::OnUpdate, this, _1));

  // Robot pose publisher
  this->robotStatesPub_ = this->node_->Advertise< revolve::msgs::RobotStates >(
      "~/revolve/robot_states", 50);
}

/////////////////////////////////////////////////
void WorldController::OnUpdate(const ::gazebo::common::UpdateInfo &_info)
{
  if (not this->robotStatesPubFreq_)
  {
    return;
  }

  auto secs = 1.0 / this->robotStatesPubFreq_;
  auto time = _info.simTime.Double();
  if ((time - this->lastRobotStatesUpdateTime_) >= secs)
  {
    // Send robot info update message, this only sends the
    // main pose of the robot (which is all we need for now)
    msgs::RobotStates msg;
    gz::msgs::Set(msg.mutable_time(), _info.simTime);

    for (auto model : this->world_->GetModels())
    {
      if (model->IsStatic())
      {
        // Ignore static models such as the ground and obstacles
        continue;
      }

      msgs::RobotState *stateMsg = msg.add_robot_state();
      stateMsg->set_name(model->GetScopedName());
      stateMsg->set_id(model->GetId());

      gz::msgs::Pose *poseMsg = stateMsg->mutable_pose();
      gz::msgs::Set(poseMsg, model->GetRelativePose().Ign());
    }

    if (msg.robot_state_size() > 0)
    {
      this->robotStatesPub_->Publish(msg);
      this->lastRobotStatesUpdateTime_ = time;
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

    auto model = this->world_->GetModel(name);
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

      this->deleteMutex_.lock();
      this->deleteMap_[id] = request->id();
      this->deleteMutex_.unlock();

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

    // Get the model name, store in the expected map
    auto name = robotSDF.Root()->GetElement("model")->GetAttribute("name")
                        ->GetAsString();

    this->insertMutex_.lock();
    this->insertMap_[name] = request->id();
    this->insertMutex_.unlock();

    this->world_->InsertModelString(robotSDF.ToString());

    // Don't leak memory
    // https://bitbucket.org/osrf/sdformat/issues/104/memory-leak-in-element
    robotSDF.Root()->Reset();
  }
  else if (request->request() == "set_robot_state_update_frequency")
  {
    this->robotStatesPubFreq_ = boost::lexical_cast< unsigned int >(
        request->data());
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
  gz::msgs::Set(inserted.mutable_time(), this->world_->GetSimTime());
  inserted.SerializeToString(resp.mutable_serialized_data());

  this->responsePub_->Publish(resp);

  std::cout << "Model `" << name << "` inserted, world now contains "
            << this->world_->GetModelCount() << " models." << std::endl;
}

/////////////////////////////////////////////////
void WorldController::HandleResponse(ConstResponsePtr &response)
{
  if (response->request() not_eq "entity_delete")
  {
    return;
  }

  int id;
  {
    boost::mutex::scoped_lock lock(this->deleteMutex_);
    if (this->deleteMap_.count(response->id()) <= 0)
    {
      return;
    }

    id = this->deleteMap_[response->id()];
    this->deleteMap_.erase(id);
  }

  gz::msgs::Response resp;
  resp.set_id(id);
  resp.set_request("delete_robot");
  resp.set_response("success");
  this->responsePub_->Publish(resp);
}
