#include <boost/bind.hpp>
#include <boost/lexical_cast.hpp>

#include "BodyAnalyzer.h"
#include <sstream>
#include <stdexcept>

namespace gz = gazebo;

namespace revolve {
namespace gazebo {

void BodyAnalyzer::Load(gz::physics::WorldPtr world, sdf::ElementPtr /*_sdf*/) {
	std::cout << "Body analyzer loaded, accepting requests..." << std::endl;

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

	// Since models are added asynchronously, we need some way of detecting our model add.
	// We do this using a model info subscriber.
	modelSub_ = node_->Subscribe("~/model/info", &BodyAnalyzer::OnModel, this);

	// Removing models from the world directly results in weird errors, so we
	// also do this with a publisher.
	deletePub_ = node_->Advertise<gz::msgs::Request>("~/request");
	deleteSub_ = node_->Subscribe("~/response", &BodyAnalyzer::OnModelDelete, this);

	// Publisher for the results
	responsePub_ = node_->Advertise<msgs::SdfBodyAnalyzeResponse>("~/analyze_body/result");
}

void BodyAnalyzer::OnModel(ConstModelPtr & msg) {
	std::string expectedName = "analyze_bot_"+boost::lexical_cast<std::string>(counter_);
	if (msg->name() != expectedName) {
		throw std::runtime_error("INTERNAL ERROR: Expecting model with name '" + expectedName +
										 "', created model was '" + msg->name() + "'.");
	}

	if (world_->GetModels().size() > 1) {
		throw std::runtime_error("INERNAL ERROR: Too many models in analyzer.");
	}

	// Unpause the world so contacts will be handled
	world_->SetPaused(false);
}

void BodyAnalyzer::OnModelDelete(ConstResponsePtr & msg) {
	if (msg->request() == "entity_delete" && msg->id() == (DELETE_BASE + counter_)) {
		// We're going to check the processing state, so acquire the mutex
		std::cout << "Completed analysis request " << currentRequest_ << '.' << std::endl;
		this->Advance();
	}
}

void BodyAnalyzer::Advance() {
	processingMutex_.lock();

	// Clear current request to indicate nothing is being
	// processed, and move on to the next item if there is one.
	counter_++;
	processing_ = false;
	currentRequest_ = "";

	// ProcessQueue needs the processing mutex, release it
	processingMutex_.unlock();
	this->ProcessQueue();
}

void BodyAnalyzer::OnContacts(ConstContactsPtr &msg) {
	// Pause the world so no new contacts will come in
	world_->SetPaused(true);

	// Create a response
	msgs::SdfBodyAnalyzeResponse response;
	response.set_id(currentRequest_);

	// Add contact info
	for (auto contact : msg->contact()) {
		auto msgContact = response.add_contact();
		msgContact->set_collision1(contact.collision1());
		msgContact->set_collision2(contact.collision2());
	}

	std::string name = "analyze_bot_"+boost::lexical_cast<std::string>(counter_);
	gz::physics::ModelPtr model = world_->GetModel(name);

	if (!model) {
		std::cerr << "------------------------------------" << std::endl;
		std::cerr << "INTERNAL ERROR, contact model not found: " << name << std::endl;
		std::cerr << "Please retry this request." << std::endl;
		std::cerr << "------------------------------------" << std::endl;
		response.set_success(false);
		responsePub_->Publish(response);

		// Advance manually
		this->Advance();
		return;
	}

	// Add the bounding box to the message
	// TODO This is currently just wrong in most cases. Must file bug.
	auto bbox = model->GetCollisionBoundingBox();
	auto box = response.mutable_boundingbox();
	box->set_x(bbox.GetXLength());
	box->set_y(bbox.GetYLength());
	box->set_z(bbox.GetZLength());

	// Publish the message
	response.set_success(true);
	responsePub_->Publish(response);

	// Delete the model. Directly doing this causes a null pointer
	// error somehow, so we use a message instead.
	// created.
	gz::msgs::Request del;
	del.set_id(DELETE_BASE + counter_);
	del.set_data(model->GetScopedName());
	del.set_request("entity_delete");
	deletePub_->Publish(del);
}

void BodyAnalyzer::AnalyzeRequest(ConstAnalyzeRequestPtr &request) {
	boost::mutex::scoped_lock lock(queueMutex_);
	std::cout << "Received request " << request->id() << std::endl;

	if (requests_.size() >= MAX_QUEUE_SIZE) {
		std::cerr << "Ignoring request " << request->id() << ": maximum queue size ("
				  << MAX_QUEUE_SIZE <<") reached." << std::endl;
	}

	// This actually copies the message, but since everything is const
	// we don't really have a choice in that regard. This shouldn't
	// be the performance bottleneck anyway.
	requests_.push(*request);

	// Release the lock explicitly to prevent deadlock in ProcessQueue
	lock.unlock();
	this->ProcessQueue();
}

void BodyAnalyzer::ProcessQueue() {
	// Acquire mutex on queue
	boost::mutex::scoped_lock lock(queueMutex_);

	if (requests_.empty()) {
		// No requests to handle
		return;
	}

	boost::mutex::scoped_lock plock(processingMutex_);
	if (processing_) {
		// Another item is being processed, wait for it
		return;
	}

	processing_ = true;

	// Pop one request off the queue and set the
	// currently processed ID on the class
	auto request = requests_.front();
	requests_.pop();

	if (request.id().empty()) {
		std::cerr << "Ignoring analysis request with empty ID." << std::endl;
		return;
	}

	currentRequest_ = request.id();
	std::cout << "Now handling request: " << currentRequest_ << std::endl;

	// Create model SDF
	sdf::SDF robotSDF;
	robotSDF.SetFromString(request.sdf());

	// Force the model name to something we know
	std::string name = "analyze_bot_"+boost::lexical_cast<std::string>(counter_);
	robotSDF.root->GetElement("model")->GetAttribute("name")->SetFromString(name);

	// Insert the model into the world
	world_->InsertModelSDF(robotSDF);

	// Analysis will proceed once the model insertion message comes through
}

} // namespace gazebo
} // namespace revolve