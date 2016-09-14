//
// Created by elte on 6-6-15.
//

#include "revolve/gazebo/plugin/WorldController.h"

namespace gz = gazebo;

namespace revolve {
namespace gazebo {

WorldController::WorldController():
	robotStatesPubFreq_(0),
	lastRobotStatesUpdateTime_(0)
{
}

void WorldController::Load(gz::physics::WorldPtr world,
                           sdf::ElementPtr /*_sdf*/)
{
	std::cout << "World plugin loaded." << std::endl;

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

	// Bind to the world update event to perform some logic
	updateConnection_ = gz::event::Events::ConnectWorldUpdateBegin(
			boost::bind(&WorldController::OnUpdate, this, _1));

	// Robot pose publisher
	robotStatesPub_ = node_->Advertise<revolve::msgs::RobotStates>("~/revolve/robot_states", 50);
}

void WorldController::OnUpdate(const ::gazebo::common::UpdateInfo &_info)
{
	if (!robotStatesPubFreq_) {
		return;
	}

	double secs = 1.0 / robotStatesPubFreq_;
	double time = _info.simTime.Double();
	if ((time - lastRobotStatesUpdateTime_) >= secs) {
		// Send robot info update message, this only sends the
		// main pose of the robot (which is all we need for now)
		msgs::RobotStates msg;
		gz::msgs::Set(msg.mutable_time(), _info.simTime);

		for (auto model : world_->GetModels()) {
			if (model->IsStatic()) {
				// Ignore static models such as the ground and obstacles
				continue;
			}

			msgs::RobotState *stateMsg = msg.add_robot_state();
			stateMsg->set_name(model->GetScopedName());
			stateMsg->set_id(model->GetId());

			gz::msgs::Pose *poseMsg = stateMsg->mutable_pose();
			gz::msgs::Set(poseMsg, model->GetRelativePose().Ign());
		}

		if (msg.robot_state_size() > 0) {
			robotStatesPub_->Publish(msg);
			lastRobotStatesUpdateTime_ = time;
		}
	}
}

// Process insert and delete requests
void WorldController::HandleRequest(ConstRequestPtr & request)
{
	if (request->request() == "delete_robot") {
		auto name = request->data();
		std::cout << "Processing request `" << request->id()
					<< "` to delete robot `" << name << "`" << std::endl;

		gz::physics::ModelPtr model = world_->GetModel(name);
		if (model) {
			// Tell the world to remove the model
			// Using `World::RemoveModel()` from here crashes the transport library, the
			// cause of which I've yet to figure out - it has something to do
			// with race conditions where the model is used by the world while
			// it is being updated. Fixing this completely appears to be a rather
			// involved process, instead, we'll use an `entity_delete` request,
			// which will make sure deleting the model happens on the world thread.
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
	} else if (request->request() == "set_robot_state_update_frequency") {
		robotStatesPubFreq_ = boost::lexical_cast<unsigned int>(request->data());
		std::cout << "Setting robot state update frequency to " << robotStatesPubFreq_ << "." << std::endl;

		gz::msgs::Response resp;
		resp.set_id(request->id());
		resp.set_request("set_robot_state_update_frequency");
		resp.set_response("success");

		responsePub_->Publish(resp);
	}
}

void WorldController::OnModel(ConstModelPtr &msg)
{
	auto name = msg->name();

	int id;
	{
		boost::mutex::scoped_lock lock(insertMutex_);
		if (insertMap_.count(name) <= 0) {
			// Insert was not requested here, ignore it
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

	std::cout << "Model `" << name << "` inserted, world now contains " <<
			world_->GetModelCount() << " models." << std::endl;
}

void WorldController::HandleResponse(ConstResponsePtr &response)
{
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
