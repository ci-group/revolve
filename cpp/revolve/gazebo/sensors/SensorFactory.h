/*
 * SensorFactory.h
 *
 *  Created on: Mar 24, 2015
 *      Author: elte
 */

#ifndef REVOLVE_GAZEBO_SENSORS_SENSORFACTORY_H_
#define REVOLVE_GAZEBO_SENSORS_SENSORFACTORY_H_

#include <revolve/gazebo/Types.h>
#include <gazebo/common/common.hh>

namespace revolve {
namespace gazebo {

class SensorFactory {
private:
	// Singleton
	SensorFactory();
public:
	virtual ~SensorFactory();

	/**
	 * Creates a new sensor in the given model, from the
	 * given SDF element pointer.
	 */
	static SensorPtr create(sdf::ElementPtr sensor,
			::gazebo::physics::ModelPtr model);
};

} /* namespace gazebo */
} /* namespace revolve */

#endif /* REVOLVE_GAZEBO_SENSORS_SENSORFACTORY_H_ */
