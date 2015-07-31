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
	void InsertRequest(ConstRequestPtr &request);

	// Callback for model insertion
	void OnModel(ConstModelPtr &msg);

	// Maps model names to insert request IDs
	std::map<std::string, int> insertMap_;

	// Stores the world
	::gazebo::physics::WorldPtr world_;

	// Transport node
	::gazebo::transport::NodePtr node_;

	// Mutex for the insertMap_
	boost::mutex insertMutex_;

	// Model insert request subscriber
	::gazebo::transport::SubscriberPtr insertSub_;

	// Model insert publisher
	::gazebo::transport::PublisherPtr insertedPub_;

	// Subscriber for actual model insertion
	::gazebo::transport::SubscriberPtr modelSub_;
};

} // namespace gazebo
} // namespace revolve

#endif //REVOLVE_WORLDCONTROLLER_H
