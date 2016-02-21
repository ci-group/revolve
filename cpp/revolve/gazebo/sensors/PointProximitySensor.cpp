#include "PointProximitySensor.h"

namespace gz = gazebo;

namespace revolve {
namespace gazebo {

PointProximitySensor::PointProximitySensor(sdf::ElementPtr sensor, ::gazebo::physics::ModelPtr model,
										   std::string partId, std::string sensorId):
		VirtualSensor(model, partId, sensorId, 1) {

	if (!sensor->HasElement("rv:point")) {
		std::cerr << "PointProximitySensor missing `rv:point` tag" << std::endl;
	}

	auto pointElem = sensor->GetElement("rv:point");
	this->point_ = pointElem->Get< gz::math::Vector3 >();
}

///////////////////////////////////

void PointProximitySensor::read(double * input) {
	input[0] = this->model_->GetWorldPose().pos.Distance(this->point_);
}

}
}