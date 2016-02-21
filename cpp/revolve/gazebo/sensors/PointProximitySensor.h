/**
 * Sensor that measures proximity to a fixed, predefined point. This can
 * for instance be used to give a robot a sense of distance to a charging station.
 */

#ifndef REVOLVE_POINTPROXIMITYSENSOR_H
#define REVOLVE_POINTPROXIMITYSENSOR_H


#include "VirtualSensor.h"

namespace revolve {
namespace gazebo {

class PointProximitySensor : public VirtualSensor {

public:
	PointProximitySensor(sdf::ElementPtr sensor, ::gazebo::physics::ModelPtr model,
						 std::string partId, std::string sensorId);

	// Reads the battery value
	virtual void read(double * input);

protected:
	/**
	 * The point to which proximity should be returned
	 */
	::gazebo::math::Vector3 point_;
};

}
}


#endif //REVOLVE_POINTPROXIMITYSENSOR_H
