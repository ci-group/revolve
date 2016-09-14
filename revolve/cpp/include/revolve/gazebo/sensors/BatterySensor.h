/**
 * Sensor that reads the battery state out of the model SDF
 */

#ifndef REVOLVE_BATTERYSENSOR_H
#define REVOLVE_BATTERYSENSOR_H

#include "VirtualSensor.h"

namespace revolve {
namespace gazebo {

class BatterySensor : public VirtualSensor {

public:
	BatterySensor(::gazebo::physics::ModelPtr model,
				  std::string partId,
				  std::string sensorId);

	// Reads the battery value
	virtual void read(double * input);

protected:
	sdf::ElementPtr batteryElem;
};

}
}

#endif //REVOLVE_BATTERYSENSOR_H
