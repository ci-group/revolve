#include "revolve/gazebo/sensors/PointIntensitySensor.h"

namespace gz = gazebo;

namespace revolve {
namespace gazebo {

PointIntensitySensor::PointIntensitySensor(sdf::ElementPtr sensor,
										   ::gazebo::physics::ModelPtr model,
										   std::string partId,
										   std::string sensorId):
		VirtualSensor(model, partId, sensorId, 1),
		i_max_(1),
		r_(1)
{

	if (!sensor->HasElement("rv:point_intensity_sensor")) {
		std::cerr << "PointIntensitySensor missing `rv:point_intensity_sensor` element." << std::endl;
		throw std::runtime_error("Robot brain error.");
	}

	auto configElem = sensor->GetElement("rv:point_intensity_sensor");

	if (!configElem->HasElement("rv:point")) {
		std::cerr << "PointIntensitySensor missing `rv:point` element." << std::endl;
	}

	auto pointElem = configElem->GetElement("rv:point");
	this->point_ = pointElem->Get< gz::math::Vector3 >();

	if (configElem->HasElement("rv:function")) {
		auto funcElem = configElem->GetElement("rv:function");

		if (funcElem->HasAttribute("r")) {
			funcElem->GetAttribute("r")->Get(this->r_);
		}

		if (funcElem->HasAttribute("i_max")) {
			funcElem->GetAttribute("i_max")->Get(this->i_max_);
		}
	}
}

///////////////////////////////////

void PointIntensitySensor::read(double * input)
{
	double distance = this->model_->GetWorldPose().pos.Distance(this->point_);

	if (distance < this->r_) {
		input[0] = this->i_max_;
	} else {
		input[0] = this->i_max_ * pow(this->r_ / distance, 2);
	}
}

}
}