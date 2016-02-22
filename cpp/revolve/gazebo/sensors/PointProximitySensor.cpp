#include "PointProximitySensor.h"

namespace gz = gazebo;

namespace revolve {
namespace gazebo {

PointProximitySensor::PointProximitySensor(sdf::ElementPtr sensor, ::gazebo::physics::ModelPtr model,
										   std::string partId, std::string sensorId):
		VirtualSensor(model, partId, sensorId, 1),
		a_(1),
		b_(1),
		c_(1)
{

	if (!sensor->HasElement("rv:point_proximity_sensor")) {
		std::cerr << "PointProximitySensor missing `rv:point_proximity_sensor` element." << std::endl;
		throw std::runtime_error("Robot brain error.");
	}

	auto configElem = sensor->GetElement("rv:point_proximity_sensor");

	if (!configElem->HasElement("rv:point")) {
		std::cerr << "PointProximitySensor missing `rv:point` element." << std::endl;
	}

	auto pointElem = configElem->GetElement("rv:point");
	this->point_ = pointElem->Get< gz::math::Vector3 >();

	if (configElem->HasElement("rv:function")) {
		auto funcElem = sensor->GetElement("rv:function");

		if (funcElem->HasAttribute("a")) {
			funcElem->GetAttribute("a")->Get(this->a_);
		}

		if (funcElem->HasAttribute("b")) {
			funcElem->GetAttribute("b")->Get(this->b_);
		}

		if (funcElem->HasAttribute("c")) {
			funcElem->GetAttribute("c")->Get(this->c_);
		}
	}
}

///////////////////////////////////

void PointProximitySensor::read(double * input) {
	double distance = this->model_->GetWorldPose().pos.Distance(this->point_);
	input[0] = this->b_ * pow(this->a_ * distance, this->c_);
}

}
}