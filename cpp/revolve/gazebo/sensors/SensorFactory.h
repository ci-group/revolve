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
public:
	SensorFactory(::gazebo::physics::ModelPtr model);
	virtual ~SensorFactory();

	/**
	 * Returns a sensor pointer instance from a motor element, part ID and type.
	 * This is the convenience wrapper over `create` that has required attributes
	 * already checked, usually you should override this when adding new sensor types.
	 */
	virtual SensorPtr getSensor(sdf::ElementPtr sensor, const std::string & type,
								const std::string & partId, const std::string & sensorId);

	/**
	 * Creates a new sensor in the given model, from the
	 * given SDF element pointer.
	 */
	virtual SensorPtr create(sdf::ElementPtr sensor);
protected:
	/**
	 * Robot model for which this factory is generating sensors.
	 */
	::gazebo::physics::ModelPtr model_;
};

} /* namespace gazebo */
} /* namespace revolve */

#endif /* REVOLVE_GAZEBO_SENSORS_SENSORFACTORY_H_ */
