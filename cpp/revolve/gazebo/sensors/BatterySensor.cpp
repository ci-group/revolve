#include "BatterySensor.h"

namespace gz = gazebo;

namespace revolve {
namespace gazebo {

BatterySensor::BatterySensor(::gazebo::physics::ModelPtr model, std::string partId,
							 std::string sensorId):
		VirtualSensor(model, partId, sensorId, 1) {
	// Find the revolve plugin to get the battery data
	auto modelSdf = model->GetSDF();
	if (modelSdf->HasElement("plugin")) {
		auto pluginElem = modelSdf->GetElement("plugin");
		while (pluginElem) {
			if (pluginElem->HasElement("rv:settings")) {
				// Found revolve plugin
				auto settings = pluginElem->GetElement("rv:settings");
				if (settings->HasElement("rv:battery")) {
					batteryElem = settings->GetElement("rv:battery");
				}

				break;
			}
			pluginElem = pluginElem->GetNextElement("plugin");
		}
	}
}

///////////////////////////////////

void BatterySensor::read(double * input) {
	if (!this->batteryElem) {
		input[0] = 0;
		return;
	}

	double maxLevel = this->batteryElem->HasElement("rv:max_level") ?
					  this->batteryElem->GetElement("rv:max_level")->Get< double >() : 0.0;
	double level = this->batteryElem->HasElement("rv:level") ?
					  this->batteryElem->GetElement("rv:level")->Get< double >() : 0.0;

	if (maxLevel < 1e-5) {
		input[0] = 0;
		return;
	}

	input[0] = level / maxLevel;
}

}
}