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

#include <queue>

// Protobuf analysis messages
#include "sdf_body_analyze.pb.h"

namespace revolve {
namespace gazebo {

typedef const boost::shared_ptr<const msgs::SdfBodyAnalyzeRequest> ConstAnalyzeRequestPtr;

class BodyAnalyzer : public ::gazebo::WorldPlugin {
public:
	void Load(::gazebo::physics::WorldPtr _parent, sdf::ElementPtr _sdf);

	// Listener for analysis requests
	void AnalyzeRequest(ConstAnalyzeRequestPtr &request);

private:
	// Processes the items in the queue if possible
	void ProcessQueue();

	/**
	 * Analyze request queue.
	 */
	std::queue<msgs::SdfBodyAnalyzeRequest> requests_;

	// ID of the current robot being evaluated, set to
	// an empty string once analysis is complete.
	std::string currentBot_;

	/// \brief Callback for contact messages from the physics engine.
	void OnContacts(ConstContactsPtr &_msg);

	// Pointer to the world
	::gazebo::physics::WorldPtr world_;

	// Transport nodes for the contact messages
	::gazebo::transport::NodePtr node_;

	// Subscriber for analysis request messages
	::gazebo::transport::SubscriberPtr requestSub_;

	// Subscriber for contacts messages
	::gazebo::transport::SubscriberPtr contactsSub_;

	// Publisher for the responses
	::gazebo::transport::PublisherPtr responsePub_;
};

}
}

#endif //REVOLVE_BODYANALYZER_H
