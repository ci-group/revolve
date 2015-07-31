//
// Created by elte on 6-6-15.
//

#include "WorldController.h"
#include <iostream>

namespace gz = gazebo;

namespace revolve {
namespace gazebo {



void WorldController::Load(gz::physics::WorldPtr world, sdf::ElementPtr /*_sdf*/) {
	std::cout << "World plugin loaded." << std::endl;

	// Store the world
	world_ = world;

	// Create transport node
	node_.reset(new gz::transport::Node());
	node_->Init();

	// Subscribe to insert request messages
	insertSub_ = node_->Subscribe("~/request", &WorldController::InsertRequest, this);

	// Publisher for inserted models
	insertedPub_ = node_->Advertise<gz::msgs::Response>("~/response");

	// Since models are added asynchronously, we need some way of detecting our model add.
	// We do this using a model info subscriber.
	modelSub_ = node_->Subscribe("~/model/info", &WorldController::OnModel, this);
}

void WorldController::InsertRequest(ConstRequestPtr & request) {
	if (request->request() != "insert_sdf") {
		return;
	}

	std::cout << "Processing insert model request ID `" << request->id() << "`." << std::endl;
	sdf::SDF robotSDF;
	robotSDF.SetFromString(request->data());

	// Get the model name, store in the expected map
	auto name = robotSDF.root->GetElement("model")->GetAttribute("name")->GetAsString();

	insertMutex_.lock();
	insertMap_[name] = request->id();
	insertMutex_.unlock();

	world_->InsertModelSDF(robotSDF);
}

void WorldController::OnModel(ConstModelPtr &msg) {
	auto name = msg->name();

	insertMutex_.lock();
	auto it = insertMap_.find(name);
	if (it == insertMap_.end()) {
		std::cout << "Insertion of model `" << name << "` was not requested here." << std::endl;
		insertMutex_.unlock();
		return;
	}

	auto id = insertMap_[name];
	insertMap_.erase(name);
	insertMutex_.unlock();

	// Respond with the inserted model
	gz::msgs::Response resp;
	resp.set_request("insert_sdf");
	resp.set_response("success");
	resp.set_id(id);

	msgs::ModelInserted inserted;
	inserted.mutable_model()->CopyFrom(*msg);
	gz::msgs::Set(inserted.mutable_time(), world_->GetSimTime());
	inserted.SerializeToString(resp.mutable_serialized_data());

	insertedPub_->Publish(resp);
}

} // namespace gazebo
} // namespace revolve
