//
// Created by elte on 6-6-15.
//

#include "WorldController.h"
#include "revolve/gazebo/gzsensors/FixedContactSensor.h"

#include <iostream>

namespace gz = gazebo;

void RegisterFixedContactSensor();

namespace revolve {
namespace gazebo {

void WorldController::Load(gz::physics::WorldPtr world, sdf::ElementPtr /*_sdf*/) {
	std::cout << "World plugin loaded." << std::endl;
	RegisterFixedContactSensor();

	// Store the world
	world_ = world;

	// Create transport node
	node_.reset(new gz::transport::Node());
	node_->Init();

	// Subscribe to insert request messages
	requestSub_ = node_->Subscribe("~/request", &WorldController::HandleRequest, this);

	// Publisher for `entity_delete` requests.
	requestPub_ = node_->Advertise<gz::msgs::Request>("~/request");

	// Publisher for inserted models
	responseSub_ = node_->Subscribe("~/response", &WorldController::HandleResponse, this);

	// Publisher for inserted models
	responsePub_ = node_->Advertise<gz::msgs::Response>("~/response");

	// Since models are added asynchronously, we need some way of detecting our model add.
	// We do this using a model info subscriber.
	modelSub_ = node_->Subscribe("~/model/info", &WorldController::OnModel, this);
}

// Process insert and delete requests
void WorldController::HandleRequest(ConstRequestPtr & request) {
	if (request->request() == "delete_robot") {
		auto name = request->data();
		std::cout << "Processing request `" << request->id()
					<< "` to delete robot `" << name << "`" << std::endl;

		gz::physics::ModelPtr model = world_->GetModel(name);
		if (model) {
			// Call `Reset` on the SDF pointer to prevent segfault
			// https://bitbucket.org/osrf/gazebo/issues/1629/removing-model-from-plugin-crashes-with#comment-21184816
			model->GetSDF()->Reset();

			// Tell the world to remove the model
			// Using the simple approach below crashes the transport library, the
			// cause of which I've yet to figure out.
			// Instead, we'll use an `entity_delete` request, catch it later on
			// and respond
			// world_->RemoveModel(model);
			gz::msgs::Request deleteReq;
			int id = gz::physics::getUniqueId();
			deleteReq.set_id(id);
			deleteReq.set_request("entity_delete");
			deleteReq.set_data(model->GetScopedName());

			deleteMutex_.lock();
			deleteMap_[id] = request->id();
			deleteMutex_.unlock();

			requestPub_->Publish(deleteReq);
		} else {
			std::cerr << "Model `" << name << "` could not be found in the world." << std::endl;
			gz::msgs::Response resp;
			resp.set_id(request->id());
			resp.set_request("delete_robot");
			resp.set_response("error");
			responsePub_->Publish(resp);
		}
	} else if (request->request() == "insert_sdf") {
		std::cout << "Processing insert model request ID `" << request->id() << "`." << std::endl;
		sdf::SDF robotSDF;
		robotSDF.SetFromString(request->data());

		// Get the model name, store in the expected map
		auto name = robotSDF.Root()->GetElement("model")->GetAttribute("name")->GetAsString();

		insertMutex_.lock();
		insertMap_[name] = request->id();
		insertMutex_.unlock();

		world_->InsertModelString(robotSDF.ToString());

		// Don't leak memory
		// https://bitbucket.org/osrf/sdformat/issues/104/memory-leak-in-element
		robotSDF.Root()->Reset();
	}
}

void WorldController::OnModel(ConstModelPtr &msg) {
	auto name = msg->name();

	int id;
	{
		boost::mutex::scoped_lock lock(insertMutex_);
		if (insertMap_.count(name) <= 0) {
			std::cout << "Insertion of model `" << name << "` was not requested here." << std::endl;
			return;
		}
		id = insertMap_[name];
		insertMap_.erase(name);
	}

	// Respond with the inserted model
	gz::msgs::Response resp;
	resp.set_request("insert_sdf");
	resp.set_response("success");
	resp.set_id(id);

	msgs::ModelInserted inserted;
	inserted.mutable_model()->CopyFrom(*msg);
	gz::msgs::Set(inserted.mutable_time(), world_->GetSimTime());
	inserted.SerializeToString(resp.mutable_serialized_data());

	responsePub_->Publish(resp);
}

void WorldController::HandleResponse(ConstResponsePtr &response) {
	if (response->request() != "entity_delete") {
		return;
	}

	int id;
	{
		boost::mutex::scoped_lock lock(deleteMutex_);
		if (deleteMap_.count(response->id()) <= 0) {
			return;
		}

		id = deleteMap_[response->id()];
		deleteMap_.erase(id);
	}

	gz::msgs::Response resp;
	resp.set_id(id);
	resp.set_request("delete_robot");
	resp.set_response("success");
	responsePub_->Publish(resp);
}

} // namespace gazebo
} // namespace revolve
