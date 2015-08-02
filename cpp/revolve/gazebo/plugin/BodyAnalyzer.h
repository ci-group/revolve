/**
 * The body analyzer can be used to gather some statistics about
 * robot bodies before actually using them. This analyzer does
 * the following:
 *
 * - It listens to incoming analyze messages TODO message type
 * - It publishes a message with robot statistics, currently all
 *   registered contacts (which can be used to identify intersecting
 *   body parts) and the robot model's bounding box.
 *
 * TODO message type
 *
 * @author Elte Hupkes
 */

#ifndef REVOLVE_BODYANALYZER_H
#define REVOLVE_BODYANALYZER_H

#include <gazebo/physics/physics.hh>
#include <gazebo/common/common.hh>
#include <gazebo/gazebo.hh>
#include <gazebo/msgs/msgs.hh>

#include <queue>
#include <utility>
#include <boost/thread/mutex.hpp>

// Protobuf analysis messages
#include <revolve/msgs/sdf_body_analyze.pb.h>

namespace revolve {
namespace gazebo {

class BodyAnalyzer : public ::gazebo::WorldPlugin {
public:
	void Load(::gazebo::physics::WorldPtr _parent, sdf::ElementPtr _sdf);

	// Maximum size of request queue, if more requests come in they are discarded
	static const int MAX_QUEUE_SIZE = 100;
private:
	// HACK: Use this as an ID "prefix" to make sure we don't
	// erroneously identify other response messages as our
	// delete requests.
	static const int DELETE_BASE = 8888888;

	// Processes the items in the queue if possible
	void ProcessQueue();

	/// Callback for contact messages from the physics engine.
	void OnContacts(ConstContactsPtr &_msg);

	// Callback for model insertion
	void OnModel(ConstModelPtr &_msg);

	// Callback for model insertion
	void OnModelDelete(ConstResponsePtr &_msg);

	// Listener for analysis requests
	void AnalyzeRequest(ConstRequestPtr &request);

	// Advances the request queue
	void Advance();

	/**
	 * Analyze request queue.
	 */
	std::queue<std::pair<int, std::string>> requests_;

	// In case message handling is fully threaded (I'm not 100% certain
	// at this point) no two threads should be allowed to modify the
	// queue at the same time, so we protect methods doing this with
	// a mutex.
	boost::mutex queueMutex_;

	// We add another mutex that is only released once a next item
	// can be processed.
	bool processing_ = false;
	boost::mutex processingMutex_;

	// Internal counter for the number of analyzed models
	int counter_ = 0;

	// ID of the current request being evaluated
	int currentRequest_;

	// Pointer to the world
	::gazebo::physics::WorldPtr world_;

	// Transport nodes for the contact messages
	::gazebo::transport::NodePtr node_;

	// Subscriber for analysis request messages
	::gazebo::transport::SubscriberPtr requestSub_;

	// Subscriber for contacts messages
	::gazebo::transport::SubscriberPtr contactsSub_;

	// Subscriber for model insertion
	::gazebo::transport::SubscriberPtr modelSub_;

	// Publisher for the responses
	::gazebo::transport::PublisherPtr responsePub_;

	// Listen to delete responses
	::gazebo::transport::SubscriberPtr deleteSub_;
};

}
}

#endif //REVOLVE_BODYANALYZER_H
