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
    : enable_parallelization(false)
    , insertMap_()
    , world_(nullptr)
    , node_(nullptr)
    , insertMutex_()
    , requestSub_(nullptr)
    , requestPub_(nullptr)
    , responseSub_(nullptr)
    , responsePub_(nullptr)
    , modelSub_(nullptr)
    , robotLearningStatesSub(nullptr)
    , onBeginUpdateConnection(nullptr)
    , onEndUpdateConnection(nullptr)
    , models_to_remove()
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
    unsubscribe(this->robotLearningStatesSub);
    fini(this->requestPub_);
    fini(this->responsePub_);
}

/////////////////////////////////////////////////
void WorldController::Load(
        gz::physics::WorldPtr world,
        sdf::ElementPtr /*_sdf*/)
{
    gz::physics::PhysicsEnginePtr physicsEngine = world->Physics();
    assert(physicsEngine != nullptr && "Physics Engine is nullptr");

    // Turn on threading
    if (this->enable_parallelization) {
        physicsEngine->SetParam("thread_position_correction", true);
        physicsEngine->SetParam("island_threads", 8);
    }

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
    this->requestPub_ = this->node_->Advertise<gz::msgs::Request>(
            "~/request");

    // Publisher for inserted models
    this->responseSub_ = this->node_->Subscribe(
            "~/response",
            &WorldController::HandleResponse,
            this);

    // Publisher for inserted models
    this->responsePub_ = this->node_->Advertise<gz::msgs::Response>(
            "~/response");

    // Since models are added asynchronously, we need some way of detecting
    // our model add. We do this using a model info subscriber.
    this->modelSub_ = this->node_->Subscribe(
            "~/model/info",
            &WorldController::OnModel,
            this);

    // Bind to the world update event to perform some logic
    this->onBeginUpdateConnection = gz::event::Events::ConnectWorldUpdateBegin(
            [this](const ::gazebo::common::UpdateInfo &_info) { this->OnBeginUpdate(_info); });

    // Bind to the world update event to perform some logic
    this->onEndUpdateConnection = gz::event::Events::ConnectWorldUpdateEnd(
            [this]() { this->OnEndUpdate(); });

    // Robot reports subscription
    this->robotLearningStatesSub = this->node_->Subscribe<revolve::msgs::LearningRobotStates>(
            "~/revolve/robot_reports",
            &WorldController::OnRobotReport,
            this);

    std::cout << "World plugin loaded." << std::endl;
}

void WorldController::Reset()
{}

/////////////////////////////////////////////////
void WorldController::OnBeginUpdate(const ::gazebo::common::UpdateInfo &_info)
{
    boost::recursive_mutex::scoped_lock lock_physics(*this->world_->Physics()->GetPhysicsUpdateMutex());

    if (model_remove_mutex.try_lock()) {
        for (const auto &model: this->models_to_remove) {
            gz::transport::requestNoReply(this->world_->Name(), "entity_delete", model->GetScopedName());
        }
        this->models_to_remove.clear();
        this->model_remove_mutex.unlock();
    }
}

void WorldController::OnEndUpdate()
{
}


/////////////////////////////////////////////////
// Process insert and delete requests
void WorldController::HandleRequest(ConstRequestPtr &request)
{
    const std::string &request_type = request->request();

    if (request_type == "delete_robot") {
        const std::string &name = request->data();
        std::cerr << "Removing Model `" << name << "` operation is not supported." << std::endl;
        gz::msgs::Response resp;
        resp.set_id(request->id());
        resp.set_request("delete_robot");
        resp.set_response("not_supported");
        this->responsePub_->Publish(resp);
    }
    else if (request_type == "insert_sdf")
    {
        std::cout << "Processing insert model request ID `" << request->id() << "`."
                  << std::endl;
        sdf::SDF robotSDF;
        robotSDF.SetFromString(request->data());

        // Get the model name, store in the expected map
        auto name = robotSDF.Root()
                ->GetElement("model")
                ->GetAttribute("name")
                ->GetAsString();

        {
            boost::mutex::scoped_lock lock(this->insertMutex_);
            this->insertMap_[name] = request->id();
        }

        // insert here, it's better. Here you can insert when the world is paused
        {
            boost::recursive_mutex::scoped_lock lock_physics(*this->world_->Physics()->GetPhysicsUpdateMutex());
            this->world_->InsertModelString(robotSDF.ToString());
        }

        // Don't leak memory
        // https://bitbucket.org/osrf/sdformat/issues/104/memory-leak-in-element
        robotSDF.Root()->Reset();
    }
    else if (request_type == "set_robot_state_update_frequency")
    {
        // Handle and fail this message, it could cause weird deadlocks if it's not responded properly
        auto frequency = request->data();
        assert(frequency.find_first_not_of("0123456789") == std::string::npos);
        unsigned int value = std::stoul(frequency);
        std::cout << "Ignoring command to set robot state update frequency to "
                  << value << '.' << std::endl;

        gz::msgs::Response resp;
        resp.set_id(request->id());
        resp.set_request("set_robot_state_update_frequency");
        resp.set_response("not_supported");

        this->responsePub_->Publish(resp);
    }
}

/////////////////////////////////////////////////
void WorldController::OnModel(ConstModelPtr &msg)
{
    auto name = msg->name();
    std::cout << "WorldController::OnModel(" << name << ')' << std::endl;

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

void WorldController::OnRobotReport(const boost::shared_ptr<revolve::msgs::LearningRobotStates const> &msg)
{
    if (msg->dead())
    {
        boost::mutex::scoped_lock lock(this->model_remove_mutex);
        gz::physics::ModelPtr model = world_->ModelByName(msg->id());
        this->models_to_remove.emplace_back(std::move(model));
    }
}
