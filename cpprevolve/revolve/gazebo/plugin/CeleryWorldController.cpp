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

#include "CeleryWorldController.h"

namespace gz = gazebo;

using namespace revolve::gazebo;

/////////////////////////////////////////////////
CeleryWorldController::CeleryWorldController()
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

CeleryWorldController::~CeleryWorldController()
{
    unsubscribe(this->requestSub_);
    unsubscribe(this->responseSub_);
    unsubscribe(this->modelSub_);
    unsubscribe(this->contactsSub_);
    fini(this->requestPub_);
    fini(this->responsePub_);
    fini(this->robotStatesPub_);
}

/////////////////////////////////////////////////
void CeleryWorldController::Load(
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
      &CeleryWorldController::HandleRequest,
      this);

  // Publisher for `entity_delete` requests.
  this->requestPub_ = this->node_->Advertise< gz::msgs::Request >(
      "~/request");

  // Publisher for inserted models
  this->responseSub_ = this->node_->Subscribe(
      "~/response",
      &CeleryWorldController::HandleResponse,
      this);

  // Publisher for inserted models
  this->responsePub_ = this->node_->Advertise< gz::msgs::Response >(
      "~/response");

  // Since models are added asynchronously, we need some way of detecting
  // our model add. We do this using a model info subscriber.
  this->modelSub_ = this->node_->Subscribe(
      "~/model/info",
      &CeleryWorldController::OnModel,
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

  // FROM HERE EVERYTHING WILL BE CELERY RELATED -Sam Ferwerda
  this->celeryChannel = AmqpClient::Channel::Create("localhost", 5672);

  // Weither simulator is busy or not
  this->running = false;

  // Consumer tag
  this->consumer_tag = this->celeryChannel->BasicConsume(
  /*queue*/"cpp",
  /*consumer_tag*/"",
  /*no_local*/true,
  /*no_ack*/false,
  /*exclusive*/false,
  /*message_prefetch_count*/1
  );

  // Get the port number of our experiments to make a unique queue
  this->envelope = this->celeryChannel->BasicConsumeMessage(this->consumer_tag);
  this->celeryChannel->BasicCancel(this->consumer_tag);

  this->celeryChannel->BasicAck(this->envelope);

  auto message = this->envelope->Message();
  auto body = message->Body();
  this->root.clear();

  std::cout << "ID: " << this->envelope->Message()->CorrelationId() << std::endl;

  auto parsingSuccessful = this->reader.parse( body, this->root );
  if ( !parsingSuccessful )
  {
      // report to the user the failure and their locations in the document.
      std::cout  << "Failed to parse configuration\n"
                 << this->reader.getFormattedErrorMessages();
      return;
  }
  auto name = "cpp"+root[0][0].asString();

  std::cout << "Connected to queue: " << name << std::endl;

  this->consumer_tag.clear();

  this->consumer_tag = this->celeryChannel->BasicConsume(
  /*queue*/name,
  /*consumer_tag*/"",
  /*no_local*/true,
  /*no_ack*/false,
  /*exclusive*/false,
  /*message_prefetch_count*/1
  );

  // Make the queue ready to use by reading it init message if possible
  auto message_delivered = this->celeryChannel->BasicConsumeMessage(this->consumer_tag, this->envelope, 100);
  if (message_delivered){
    this->celeryChannel->BasicAck(this->envelope);
  };

    // this->contactsSub_ = this->node_->Subscribe(
    //         "~/physics/contacts",
    //         &CeleryWorldController::OnContacts,
    //         this);

}

void CeleryWorldController::Reset()
{
    this->lastRobotStatesUpdateTime_ = 0; //this->world_->SimTime().Double();
}

/////////////////////////////////////////////////
void CeleryWorldController::OnBeginUpdate(const ::gazebo::common::UpdateInfo &_info) {
    if (not this->robotStatesPubFreq_ || not this->celeryChannel) {
        return;
    }

    auto secs = 1.0 / this->robotStatesPubFreq_;
    auto time = _info.simTime.Double();
    if ((time - this->lastRobotStatesUpdateTime_) >= secs) {
      // Send robot info update message, this only sends the
      // main pose of the robot (which is all we need for now)
      msgs::RobotStates msg;
      //gz::msgs::Set(msg.mutable_time(), _info.simTime);

      {
        boost::recursive_mutex::scoped_lock lock_physics(*this->world_->Physics()->GetPhysicsUpdateMutex());
        for (const auto &model : this->world_->Models()) {
          if (model->IsStatic()) {
            // Ignore static models such as the ground and obstacles
            continue;
          }

          revolve::msgs::RobotState *stateMsg = msg.add_robot_state();
          //const std::string scoped_name = model->GetScopedName();
          //stateMsg->set_name(scoped_name);
          //stateMsg->set_id(model->GetId());

          //auto poseMsg = stateMsg->mutable_pose();
          auto relativePose = model->RelativePose();

          //gz::msgs::Set(poseMsg, relativePose);

          // Update relative position in JSON
          boost::mutex::scoped_lock plock(dataMutex_);
          this->rootmsg["result"][0]["x"].append(relativePose.Pos().X());
          this->rootmsg["result"][0]["y"].append(relativePose.Pos().Y());
          this->rootmsg["result"][0]["z"].append(relativePose.Pos().Z());
          this->rootmsg["result"][0]["roll"].append(relativePose.Rot().Roll());
          this->rootmsg["result"][0]["pitch"].append(relativePose.Rot().Pitch());
          this->rootmsg["result"][0]["yaw"].append(relativePose.Rot().Yaw());
          this->rootmsg["result"][0]["times"].append(_info.simTime.Double());
          plock.unlock();

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
              // stateMsg->set_dead(false);
            } else {
              bool alive = death_sentence_value > time;
              // stateMsg->set_dead(not alive);

              if (not alive) {
                boost::mutex::scoped_lock lock(this->death_sentences_mutex_);
                this->death_sentences_.erase(model->GetName());

                this->models_to_remove.emplace_back(model);
              }
            }
          }
        }
      }

      if (msg.robot_state_size() > 0) {
        //this->robotStatesPub_->Publish(msg);
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

        boost::mutex::scoped_lock plock(dataMutex_);
        this->rootmsg["task_id"] = this->envelope->Message()->CorrelationId();
        this->rootmsg["status"] = "SUCCESS";

        std::string output = this->fastWriter.write(this->rootmsg);
        plock.unlock();

        std::cout << "Setting celery result for robot: " << model->GetScopedName() << std::endl;
        auto MESSAGE = AmqpClient::BasicMessage::Create(output);
        MESSAGE->ContentType("application/json");
        MESSAGE->ContentEncoding("utf-8");
        MESSAGE->ReplyTo(this->envelope->Message()->ReplyTo());
        MESSAGE->CorrelationId(this->envelope->Message()->CorrelationId());

        MESSAGE->HeaderTable({
          {"id", this->envelope->Message()->CorrelationId()},
          {"task", "tasks.insert_robot"}
        });

        this->celeryChannel->BasicPublish("", MESSAGE->ReplyTo(), MESSAGE);

        this->running = false;
      }
      this->models_to_remove.clear();
      //        this->world_insert_remove_mutex.unlock();
      //    }

}

void CeleryWorldController::OnEndUpdate()
{
//     { // check if there are robots to delete
//         std::tuple< ::gazebo::physics::ModelPtr, int> delete_robot;
//         {
//             boost::mutex::scoped_lock lock(this->deleteMutex_);
//             if (not this->delete_robot_queue.empty()) {
//                 delete_robot = this->delete_robot_queue.front();
//                 this->delete_robot_queue.pop();
//             }
//         }
//         auto model = std::get<0>(delete_robot);
//         auto request_id = std::get<1>(delete_robot);
//         if (model)
//         {
//             {
// //                boost::recursive_mutex::scoped_lock lock_physics(*this->world_->Physics()->GetPhysicsUpdateMutex());
//                 this->world_->RemoveModel(model);
//             }
//
//             gz::msgs::Response resp;
//             resp.set_id(request_id);
//             resp.set_request("delete_robot");
//             resp.set_response("success");
//             this->responsePub_->Publish(resp);
//         }
//     }

    { // check if there are robots to insert
        // celery part of inserting robot (waits for robot)
        if (not this->running){
          auto message_delivered = this->celeryChannel->BasicConsumeMessage(this->consumer_tag, this->envelope, 1000);
          if (!message_delivered){
            return;
          }
          auto message = this->envelope->Message();
          auto body = message->Body();

          bool parsingSuccessful = this->reader.parse( message->Body(), this->root );
          if ( !parsingSuccessful )
          {
              // report to the user the failure and their locations in the document.
              std::cout  << "Failed to parse configuration\n"
                         << reader.getFormattedErrorMessages();
              return;
          }
          this->celeryChannel->BasicAck(this->envelope);

          auto sdfString = this->root[0][0];
          auto lifespan_timeout = this->root[0][1];

          sdf::SDF robotSDF;
          robotSDF.SetFromString(sdfString.asString());

          std::cout << "Inserting robot into world." << std::endl;

          boost::mutex::scoped_lock plock(dataMutex_);
          // resetting last message
          this->rootmsg.clear();
          // The skeleton for message
          this->rootmsg["result"][0]["x"] = Json::arrayValue;
          this->rootmsg["result"][0]["y"] = Json::arrayValue;
          this->rootmsg["result"][0]["z"] = Json::arrayValue;
          this->rootmsg["result"][0]["roll"] = Json::arrayValue;
          this->rootmsg["result"][0]["pitch"] = Json::arrayValue;
          this->rootmsg["result"][0]["yaw"] = Json::arrayValue;
          this->rootmsg["result"][0]["times"] = Json::arrayValue;
          this->rootmsg["result"][0]["contacts"] = Json::arrayValue;

          plock.unlock();

          auto name = robotSDF.Root()->GetElement("model")->GetAttribute("name")
                              ->GetAsString();

          death_sentences_[name] = -lifespan_timeout.asDouble();

          this->world_->InsertModelString(robotSDF.ToString());

          // against memory leaking
          robotSDF.Root()->Reset();

          this->running = true;
        }


        // old revolve to insert robot
//         boost::mutex::scoped_lock lock(this->insertMutex_);
//         for (auto &iterator: this->insertMap_)
//         {
//             bool &insert_operation_pending = std::get<2>(iterator.second);
//             //std::cout << "trying to insert " << iterator.first << " - " << insert_operation_pending << std::endl;
// //            if (insert_operation_pending and this->world_insert_remove_mutex.try_lock())
//             if (insert_operation_pending)
//             {
//                 // Start insert operation!
// //                boost::recursive_mutex::scoped_lock lock_physics(*this->world_->Physics()->GetPhysicsUpdateMutex());
//                 const std::string &robotSDF = std::get<1>(iterator.second);
//                 this->world_->InsertModelString(robotSDF);
//                 insert_operation_pending = false;
//                 break;
//             }
//         }
    }
}


/////////////////////////////////////////////////
// Process insert and delete requests
void CeleryWorldController::HandleRequest(ConstRequestPtr &request)
{
  if (request->request() == "delete_robot")
  {
    auto name = request->data();
    std::cout << "Processing request `" << request->id()
              << "` to delete robot `" << name << "`" << std::endl;

//    auto model = this->world_->ModelByName(name);
//    if (model)
//    {
//      // Tell the world to remove the model
//      // Using `World::RemoveModel()` from here crashes the transport
//      // library, the cause of which I've yet to figure out - it has
//      // something to do with race conditions where the model is used by
//      // the world while it is being updated. Fixing this completely
//      // appears to be a rather involved process, instead, we'll use an
//      // `entity_delete` request, which will make sure deleting the model
//      // happens on the world thread.
//      gz::msgs::Request deleteReq;
//      auto id = gz::physics::getUniqueId();
//      deleteReq.set_id(id);
//      deleteReq.set_request("entity_delete");
//      deleteReq.set_data(model->GetScopedName());
//
//      {
//        boost::mutex::scoped_lock lock(this->deleteMutex_);
//        this->delete_robot_queue.emplace(std::make_tuple(model, request->id()));
//      }
//      {
//        boost::mutex::scoped_lock lock(this->death_sentences_mutex_);
//        this->death_sentences_.erase(model->GetName());
//      }
//
//      this->requestPub_->Publish(deleteReq);
//    }
//    else
//    {
      std::cerr << "Model `" << name << "` could not be found in the world."
                << std::endl;
      gz::msgs::Response resp;
      resp.set_id(request->id());
      resp.set_request("delete_robot");
      resp.set_response("error");
      this->responsePub_->Publish(resp);
//    }
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
      this->insertMap_[name] = std::make_tuple(request->id(), robotSDF.ToString(), true);
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
/////////////////////////////////////////////////
void CeleryWorldController::OnContacts(ConstContactsPtr &msgContact){
  // in this function I process what in the old revolve was done inside the robot manager.
  // I am not yet sure which one is faster, computing here or there. Doing this computation blocks
  // other message writing commands to celery.

  auto contactsList = msgContact->contact();
  boost::mutex::scoped_lock plock(dataMutex_);

  // //// METHOD 1: ////
  for (const auto &contact : contactsList){
    auto number_of_contacts = 0;
    for (const auto &pos : contact.position()){
        number_of_contacts++;
    }
    this->rootmsg["result"][0]["contacts"].append(number_of_contacts);
  }
  plock.unlock();

  //// METHOD 2: NOT YET IMPLEMENTED ////
  // Receiving number of contacts from the contactmanager would be more efficient.
  // because we are not using any collision information as far as I know.

}
/////////////////////////////////////////////////
void CeleryWorldController::OnModel(ConstModelPtr &msg)
{
    auto name = msg->name();
    std::cout << "CeleryWorldController::OnModel(" << name << ')' << std::endl;


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
void CeleryWorldController::HandleResponse(ConstResponsePtr &response)
{
//    std::cout << "WorldController::HandleResponse(" << response->request() << ')' << std::endl;

    if (response->request() not_eq "entity_delete")
    {
        return;
    }

//    int id;
//    {
//        boost::mutex::scoped_lock lock(this->deleteMutex_);
//        if (this->deleteMap_.count(response->id()) <= 0)
//        {
//            return;
//        }
//
//        id = this->deleteMap_[response->id()];
//        this->deleteMap_.erase(id);
//    }

//    this->world_insert_remove_mutex.unlock();

//    gz::msgs::Response resp;
//    resp.set_id(id);
//    resp.set_request("delete_robot");
//    resp.set_response("success");
//    this->responsePub_->Publish(resp);
}
