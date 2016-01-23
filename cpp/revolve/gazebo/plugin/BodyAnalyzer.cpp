#include <boost/bind.hpp>
#include <boost/lexical_cast.hpp>
#include <boost/date_time/posix_time/posix_time.hpp>
#include <boost/thread/thread.hpp>

#include "BodyAnalyzer.h"
#include <sstream>
#include <stdexcept>

namespace gz = gazebo;

namespace revolve {
namespace gazebo {

void BodyAnalyzer::Load(gz::physics::WorldPtr world, sdf::ElementPtr /*_sdf*/) {
	// Store pointer to the world
	world_ = world;

	// Pause the world if it is not already paused
	world->SetPaused(true);

	// Set initial state values
	processing_ = false;
	counter_ = 0;
	currentRequest_ = -1;

	// Create a new transport node for advertising / subscribing
	node_.reset(new gz::transport::Node());
	node_->Init();

	// Subscribe to the contacts message. Note that the contact manager does
	// not generate data without at least one subscriber, so there is no use
	// in bypassing the messaging mechanism.
	contactsSub_ = node_->Subscribe("~/physics/contacts", &BodyAnalyzer::OnContacts, this);

	// Subscribe to analysis request messages
	requestSub_ = node_->Subscribe("~/request", &BodyAnalyzer::AnalyzeRequest, this);

	// Since models are added asynchronously, we need some way of detecting our model add.
	// We do this using a model info subscriber.
	modelSub_ = node_->Subscribe("~/model/info", &BodyAnalyzer::OnModel, this);

	// Publisher for the results
	responsePub_ = node_->Advertise<gz::msgs::Response>("~/response");

	// Subscribe to model delete events
	deleteSub_ = node_->Subscribe("~/response", &BodyAnalyzer::OnModelDelete, this);

	// Hello world!
	std::cout << "Body analyzer ready" << std::endl;
}

void BodyAnalyzer::OnModel(ConstModelPtr & msg) {
	std::string expectedName = "analyze_bot_"+boost::lexical_cast<std::string>(counter_);
	if (msg->name() != expectedName) {
		throw std::runtime_error("INTERNAL ERROR: Expecting model with name '" + expectedName +
								 "', created model was '" + msg->name() + "'.");
	}

	if (world_->GetModels().size() > 1) {
		throw std::runtime_error("INTERNAL ERROR: Too many models in analyzer.");
	}

	// Unpause the world so contacts will be handled
	world_->SetPaused(false);
}

void BodyAnalyzer::OnModelDelete(ConstResponsePtr & msg) {
	if (msg->request() == "entity_delete") {
		// This might have cleared the world
		this->ProcessQueue();
	}
}

void BodyAnalyzer::Advance() {
	processingMutex_.lock();

	// Clear current request to indicate nothing is being
	// processed, and move on to the next item if there is one.
	counter_++;
	processing_ = false;
	currentRequest_ = -1;

	// ProcessQueue needs the processing mutex, release it
	processingMutex_.unlock();
	this->ProcessQueue();
}

void BodyAnalyzer::OnContacts(ConstContactsPtr &msg) {
	// Pause the world so no new contacts will come in
	world_->SetPaused(true);

	boost::mutex::scoped_lock plock(processingMutex_);
	if (!processing_) {
		return;
	}
	plock.unlock();

	if (world_->GetModelCount() > 1) {
		std::cerr << "WARNING: Too many models in the world." << std::endl;
	}

	// Create a response
	msgs::BodyAnalysisResponse response;
	gz::msgs::Response wrapper;
	wrapper.set_id(currentRequest_);
	wrapper.set_request("analyze_body");

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
		wrapper.set_response("error");
		response.SerializeToString(wrapper.mutable_serialized_data());
		responsePub_->Publish(wrapper);

		// Advance manually
		this->Advance();
		return;
	}

	// Add the bounding box to the message
	// Model collision bounding box is currently broken in Gazebo:
	// https://bitbucket.org/osrf/gazebo/issue/1325/getboundingbox-returns-the-models-last
	// My suggested fixes are present in the gazebo6-revolve branch
	auto bbox = model->GetBoundingBox();
	auto box = response.mutable_boundingbox();
	gz::msgs::Set(box->mutable_min(), bbox.min.Ign());
	gz::msgs::Set(box->mutable_max(), bbox.max.Ign());

	// Publish the message, serializing the response message in the wrapper data
	response.SerializeToString(wrapper.mutable_serialized_data());
	wrapper.set_response("success");
	responsePub_->Publish(wrapper);
	std::cout << "Response for request " << currentRequest_ << " sent." << std::endl;

	// Remove all models from the world and advance
	world_->Clear();
	this->Advance();
}

void BodyAnalyzer::AnalyzeRequest(ConstRequestPtr &request) {
	if (request->request() != "analyze_body") {
		// Request is not meant for us
		return;
	}

	if (!request->has_data()) {
		std::cerr << "An `analyze_body` request should have data." << std::endl;
		return;
	}

	// Create the request pair before locking the mutex - this seems
	// to prevent threading and "unknown message type" problems.
	std::pair<int, std::string> req(request->id(), request->data());
	std::cout << "Received request " << request->id() << std::endl;

	boost::mutex::scoped_lock lock(queueMutex_);

	if (requests_.size() >= MAX_QUEUE_SIZE) {
		std::cerr << "Ignoring request " << request->id() << ": maximum queue size ("
		<< MAX_QUEUE_SIZE <<") reached." << std::endl;
		return;
	}

	// This actually copies the message, but since everything is const
	// we don't really have a choice in that regard. This shouldn't
	// be the performance bottleneck anyway.
	requests_.push(req);

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

	if (world_->GetModelCount()) {
		// There are still some items in the world, wait until
		// `Clear()` has done its job.
		return;
	}

	processing_ = true;

	// Pop one request off the queue and set the
	// currently processed ID on the class
	auto request = requests_.front();
	requests_.pop();

	currentRequest_ = request.first;
	std::cout << "Now handling request: " << currentRequest_ << std::endl;

	// Create model SDF
	sdf::SDF robotSDF;
	robotSDF.SetFromString(request.second);

	// Force the model name to something we know
	std::string name = "analyze_bot_"+boost::lexical_cast<std::string>(counter_);
	robotSDF.Root()->GetElement("model")->GetAttribute("name")->SetFromString(name);

	// Insert the model into the world. For clarity we use `InsertModelString` directly,
	// this is actually also what `InsertModelSdf` does.
	world_->InsertModelString(robotSDF.ToString());

	// The contents of the SDF element are *not* cleared automatically
	// when robotSDF goes out of scope.
	// https://bitbucket.org/osrf/sdformat/issues/104/memory-leak-in-element
	robotSDF.Root()->Reset();

	// Analysis will proceed once the model insertion message comes through
}

} // namespace gazebo
} // namespace revolve