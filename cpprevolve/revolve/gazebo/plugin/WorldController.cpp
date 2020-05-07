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
    gz::physics::PhysicsEnginePtr physicsEngine = world->Physics();
    assert(physicsEngine != nullptr);

    // Turn on threading
    physicsEngine->SetParam("thread_position_correction", true);
    physicsEngine->SetParam("island_threads", 8);


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
}

/////////////////////////////////////////////////
void WorldController::OnBeginUpdate(const ::gazebo::common::UpdateInfo &_info) {

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
        if (model)
        {
            {
//                boost::recursive_mutex::scoped_lock lock_physics(*this->world_->Physics()->GetPhysicsUpdateMutex());
                this->world_->RemoveModel(model);
            }

            gz::msgs::Response resp;
            resp.set_id(request_id);
            resp.set_request("delete_robot");
            resp.set_response("success");
            this->responsePub_->Publish(resp);
        }
    }

    { // check if there are robots to insert
        boost::mutex::scoped_lock lock(this->insertMutex_);
        for (auto &iterator: this->insertMap_)
        {
            bool &insert_operation_pending = std::get<2>(iterator.second);
            //std::cout << "trying to insert " << iterator.first << " - " << insert_operation_pending << std::endl;
//            if (insert_operation_pending and this->world_insert_remove_mutex.try_lock())
            if (insert_operation_pending)
            {
                // Start insert operation!
//                boost::recursive_mutex::scoped_lock lock_physics(*this->world_->Physics()->GetPhysicsUpdateMutex());
                const std::string &robotSDF = std::get<1>(iterator.second);
                this->world_->InsertModelString(robotSDF);
                insert_operation_pending = false;
                break;
            }
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

    std::cerr << "Model `" << name << "` could not be found in the world."
              << std::endl;
    gz::msgs::Response resp;
    resp.set_id(request->id());
    resp.set_request("delete_robot");
    resp.set_response("error");
    this->responsePub_->Publish(resp);
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

    {
      boost::mutex::scoped_lock lock(this->insertMutex_);
      this->insertMap_[name] = std::make_tuple(request->id(), robotSDF.ToString(), true);
    }

    //TODO insert here, it's better
    //this->world_->InsertModelString(robotSDF.ToString());

    // Don't leak memory
    // https://bitbucket.org/osrf/sdformat/issues/104/memory-leak-in-element
    robotSDF.Root()->Reset();
  }
}

/////////////////////////////////////////////////
void WorldController::OnModel(ConstModelPtr &msg)
{
    auto name = msg->name();
    std::cout << "WorldController::OnModel(" << name << ')' << std::endl;


    int id;
    bool insert_operation_pending;
    {
        boost::mutex::scoped_lock lock(this->insertMutex_);
        if (this->insertMap_.count(name) <= 0)
        {
            // Insert was not requested here, ignore it
            return;
        }
        const std::tuple<int, std::string, bool> &entry = this->insertMap_[name];
        id = std::get<0>(entry);
        insert_operation_pending = std::get<2>(entry);
        if (insert_operation_pending)
        {
            // Insert operation has not been done yet
            // (but you should never be here, because we are in the "OnModel" function
            return;
        }
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

//    this->world_insert_remove_mutex.unlock();

    std::cout << "Model `" << name << "` inserted, world now contains "
              << this->world_->ModelCount() << " models." << std::endl;
}

/////////////////////////////////////////////////
void WorldController::HandleResponse(ConstResponsePtr &response)
{
//    std::cout << "WorldController::HandleResponse(" << response->request() << ')' << std::endl;

    if (response->request() not_eq "entity_delete")
    {
        return;
    }
}
