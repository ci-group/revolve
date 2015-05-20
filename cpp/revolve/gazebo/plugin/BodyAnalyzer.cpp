#include <boost/bind.hpp>

#include "BodyAnalyzer.h"

namespace gz = gazebo;

namespace revolve {
namespace gazebo {

void BodyAnalyzer::Load(gz::physics::WorldPtr world, sdf::ElementPtr /*_sdf*/) {
	std::cout << "Plugin loaded." << std::endl;

	// Store pointer to the world
	world_ = world;

	// Pause the world if it is not already paused
	world->SetPaused(true);

	// Create a new transport node for advertising / subscribing
	node_.reset(new gz::transport::Node());
	node_->Init();

	// Subscribe to the contacts message. Note that the contact manager does
	// not generate data without at least one subscriber, so there is no use
	// in bypassing the messaging mechanism.
	contactsSub_ = node_->Subscribe("~/physics/contacts", &BodyAnalyzer::OnContacts, this);

	// Subscribe to analysis request messages
	requestSub_ = node_->Subscribe("~/analyze_body/request", &BodyAnalyzer::AnalyzeRequest, this);

	// Publisher for the results
	responsePub_ = node_->Advertise<msgs::SdfBodyAnalyzeResponse>("~/analyze_body/result");
}

void BodyAnalyzer::OnContacts(ConstContactsPtr &msg) {
	msgs::SdfBodyAnalyzeResponse response;
	response.set_id(currentBot_);

	for (auto contact : msg->contact()) {
		auto msgContact = response.add_contact();
		msgContact->set_collision1(contact.collision1());
		msgContact->set_collision2(contact.collision2());
	}

	// Pause the world again
	world_->SetPaused(true);

	// Add the bounding box to the message
	auto box = response.mutable_boundingbox();
	gz::physics::ModelPtr model = world_->GetModel("analyze_bot");
	auto bbox = model->GetBoundingBox();
	box->set_x(bbox.GetXLength());
	box->set_y(bbox.GetYLength());
	box->set_z(bbox.GetZLength());

	// Publish the message
	responsePub_->Publish(response);

	// Clear current processor and move on to the next item
	// if applicable.
	currentBot_ = "";
	this->ProcessQueue();
}

void BodyAnalyzer::AnalyzeRequest(ConstAnalyzeRequestPtr &request) {
	std::cout << "Analysis request!" << std::endl;

	// This actually copies the message, but since everything is const
	// we don't really have a choice in that regard.
	requests_.push(*request);
	this->ProcessQueue();
}

void BodyAnalyzer::ProcessQueue() {
	if (!currentBot_.empty() || requests_.empty()) {
		// We're either currently processing, or there
		// are no requests.
		return;
	}

	//Pop one request off the queue and set the
	// currently processed ID on the class
	auto request = requests_.front();
	requests_.pop();
	currentBot_ = request.id();

	// Create model SDF
	sdf::SDF robotSDF;
	robotSDF.SetFromString(request.sdf());

	// Force the model name to `analyze_bot`
	robotSDF.root->GetElement("model")->GetAttribute("name")->SetFromString("analyze_bot");

	// Insert the model into the world
	world_->InsertModelSDF(robotSDF);

	// Unpause the world for the contacts to fire
	world_->SetPaused(false);
}

} // namespace gazebo
} // namespace gevolve