#include <boost/bind.hpp>

#include "BodyAnalyzer.h"
#include <sstream>
#include <stdexcept>

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

// Unpauses the world once the model has been inserted
void BodyAnalyzer::OnModel(ConstModelPtr & msg) {
	std::cout << "Model inserted: " << msg->name() << std::endl;
	std::cout << "Num models in OnModel: " << world_->GetModels().size() << std::endl;

	if (world_->GetModels().size() > 1) {
		throw std::runtime_error("Too many models.");
	}

	world_->SetPaused(false);
}

void BodyAnalyzer::OnModelDelete(ConstResponsePtr & msg) {
	std::cout << "Response: " << msg->id() << ":" << msg->request()
	 		  << ":" << msg->response() << std::endl;

	if (msg->request() == "entity_delete" && msg->id() == (DELETE_BASE + counter_)) {
		// We're going to check the processing state, so acquire the mutex
		std::cout << "Before processing lock" << std::endl;
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
}

void BodyAnalyzer::OnContacts(ConstContactsPtr &msg) {
	// Pause the world so no new contacts will come in
	world_->SetPaused(true);

	std::cout << "Contacts." << std::endl;

	// Create a response
	msgs::SdfBodyAnalyzeResponse response;
	response.set_id(currentRequest_);

	// Add contact info
	for (auto contact : msg->contact()) {
		auto msgContact = response.add_contact();
		msgContact->set_collision1(contact.collision1());
		msgContact->set_collision2(contact.collision2());
	}

	// Add the bounding box to the message
	auto box = response.mutable_boundingbox();
	std::stringstream name;
	name << "analyze_bot_" << counter_;
	gz::physics::ModelPtr model = world_->GetModel(name.str());

	if (!model) {
		std::cerr << "------------------------------------" << std::endl;
		std::cerr << "No such model man: " << name.str() << std::endl;
		std::cerr << "------------------------------------" << std::endl;
		world_->SetPaused(false);
		return;
	}

	auto bbox = model->GetBoundingBox();
	box->set_x(bbox.GetXLength());
	box->set_y(bbox.GetYLength());
	box->set_z(bbox.GetZLength());

	// Publish the message
	responsePub_->Publish(response);

	// Delete the model. Directly doing this causes a null pointer
	// error somehow, so we use a message instead.
	// created.
	gz::msgs::Request del;
	del.set_id(DELETE_BASE + counter_);
	del.set_data(model->GetScopedName());
	del.set_request("entity_delete");
	deletePub_->Publish(del);

	std::cout << "Messages sent." << std::endl;
}

void BodyAnalyzer::AnalyzeRequest(ConstAnalyzeRequestPtr &request) {
	std::cout << "Before queue mutex lock (AnalyzeRequest)" << std::endl;
	queueMutex_.lock();

	std::cout << "New request." << std::endl;

	// This actually copies the message, but since everything is const
	// we don't really have a choice in that regard. This shouldn't
	// be the performance bottleneck anyway.
	requests_.push(*request);

	// Release the lock explicitly to prevent deadlock in ProcessQueue
	queueMutex_.unlock();
	this->ProcessQueue();
}

void BodyAnalyzer::ProcessQueue() {
	// Acquire mutex on queue
	std::cout << "Before queue mutex lock (ProcessQueue)" << std::endl;
	boost::mutex::scoped_lock lock(queueMutex_);

	std::cout << "Try queue." << std::endl;

	if (requests_.empty()) {
		// No requests to handle
		std::cout << "Nothing to process." << std::endl;
		return;
	}

	std::cout << "Before processing lock (ProcessQueue)" << std::endl;
	boost::mutex::scoped_lock plock(processingMutex_);
	if (processing_) {
		// Another item is being processed, wait for it
		std::cout << "Currently processing: " << currentRequest_ << std::endl;
		return;
	}

	std::cout << "++++Pop request+++++" << std::endl;
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

	// Create model SDF
	sdf::SDF robotSDF;
	robotSDF.SetFromString(request.sdf());

	// Force the model name to `analyze_bot`
	std::stringstream name;
	name << "analyze_bot_" << counter_;
	robotSDF.root->GetElement("model")->GetAttribute("name")->SetFromString(name.str());

	// Insert the model into the world
	world_->InsertModelSDF(robotSDF);

	// Analysis will proceed once the model insertion message comes through
}

} // namespace gazebo
} // namespace gevolve