//
// Created by elte on 6-6-15.
//

#ifndef REVOLVE_WORLDCONTROLLER_H
#define REVOLVE_WORLDCONTROLLER_H

#include <gazebo/gazebo.hh>
#include <gazebo/physics/physics.hh>
#include <gazebo/common/common.hh>
#include <gazebo/msgs/msgs.hh>

#include <revolve/msgs/insert_sdf_robot.pb.h>

namespace revolve {
namespace gazebo {

typedef const boost::shared_ptr<const ::revolve::msgs::InsertSdfRobotRequest> ConstInsertSdfRobotRequestPtr;

class WorldController : public ::gazebo::WorldPlugin {
public:
	void Load(::gazebo::physics::WorldPtr _parent, sdf::ElementPtr _sdf);

protected:
	// Listener for analysis requests
	void InsertRequest(ConstInsertSdfRobotRequestPtr &request);

	// Stores the world
	::gazebo::physics::WorldPtr world_;

	// Transport node
	::gazebo::transport::NodePtr node_;

	// Subscriber
	::gazebo::transport::SubscriberPtr insertSub_;
};

} // namespace gazebo
} // namespace revolve

#endif //REVOLVE_WORLDCONTROLLER_H
