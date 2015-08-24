//
// Created by elte on 6-6-15.
//

#ifndef REVOLVE_WORLDCONTROLLER_H
#define REVOLVE_WORLDCONTROLLER_H

#include <gazebo/gazebo.hh>
#include <gazebo/physics/physics.hh>
#include <gazebo/common/common.hh>
#include <gazebo/msgs/msgs.hh>

#include <revolve/msgs/model_inserted.pb.h>

#include <boost/thread/mutex.hpp>

namespace revolve {
namespace gazebo {

class WorldController : public ::gazebo::WorldPlugin {
public:
	void Load(::gazebo::physics::WorldPtr _parent, sdf::ElementPtr _sdf);

protected:
	// Listener for analysis requests
	void HandleRequest(ConstRequestPtr &request);

	// Listener for entity delete responses
	void HandleResponse(ConstResponsePtr &request);

	// Callback for model insertion
	void OnModel(ConstModelPtr &msg);

	// Maps model names to insert request IDs
	std::map<std::string, int> insertMap_;

	// Maps `entity_delete` IDs to `delete_robot` ids
	std::map<int, int> deleteMap_;

	// Stores the world
	::gazebo::physics::WorldPtr world_;

	// Transport node
	::gazebo::transport::NodePtr node_;

	// Mutex for the insertMap_
	boost::mutex insertMutex_;

	// Mutex for the deleteMap_
	boost::mutex deleteMutex_;

	// Request subscriber
	::gazebo::transport::SubscriberPtr requestSub_;

	// Request publisher
	::gazebo::transport::PublisherPtr requestPub_;

	// Response subscriber
	::gazebo::transport::SubscriberPtr responseSub_;

	// Response publisher
	::gazebo::transport::PublisherPtr responsePub_;

	// Subscriber for actual model insertion
	::gazebo::transport::SubscriberPtr modelSub_;
};

} // namespace gazebo
} // namespace revolve

#endif //REVOLVE_WORLDCONTROLLER_H
