//
// Created by elte on 6-6-15.
//

#include "WorldController.h"
#include <iostream>

namespace gz = gazebo;

namespace revolve {
namespace gazebo {



void WorldController::Load(gz::physics::WorldPtr world, sdf::ElementPtr /*_sdf*/) {
	std::cout << "World plugin loaded." << std::endl;

	// Store the world
	world_ = world;

	// Create transport node
	node_.reset(new gz::transport::Node());
	node_->Init();

	// Subscribe to insert request messages
	insertSub_ = node_->Subscribe("~/insert_robot_sdf/request",
								  &WorldController::InsertRequest, this);
}

void WorldController::InsertRequest(ConstInsertSdfModelRequestPtr & request) {
	std::cout << "Attempting to create and insert robot `" << request->name() << "`." << std::endl;
	sdf::SDF robotSDF;
	robotSDF.SetFromString(request->sdf_contents());

	// Fix the name in case it doesn't match
	sdf::ElementPtr model = robotSDF.root->GetElement("model");
	model->GetAttribute("name")->SetFromString(request->name());

	world_->InsertModelSDF(robotSDF);
}

} // namespace gazebo
} // namespace revolve
