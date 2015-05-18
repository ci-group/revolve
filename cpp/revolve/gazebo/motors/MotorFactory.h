/*
 * MotorFactory.h
 *
 *  Created on: Mar 16, 2015
 *      Author: elte
 */

#ifndef REVOLVE_GAZEBO_MOTORS_MOTORFACTORY_H_
#define REVOLVE_GAZEBO_MOTORS_MOTORFACTORY_H_

#include <revolve/gazebo/Types.h>

#include <gazebo/common/common.hh>

namespace revolve {
namespace gazebo {

class MotorFactory {
public:
	MotorFactory(::gazebo::physics::ModelPtr model);
	virtual ~MotorFactory();

	/**
	 * Returns a motor pointer instance from a motor element, part ID and type.
	 * This is the convenience wrapper over `create` that has required attributes
	 * already checked, usually you should override this when adding new motor types.
	 */
	virtual MotorPtr getMotor(sdf::ElementPtr motor, const std::string & type,
							  const std::string & motorId, const std::string & partId);

	/**
	 * Creates a motor for the given model for the given SDF element.
	 */
	virtual MotorPtr create(sdf::ElementPtr motor);

protected:
	/**
	 * Internal reference to the robot model
	 */
	::gazebo::physics::ModelPtr model_;
};

} /* namespace gazebo */
} /* namespace revolve */

#endif /* REVOLVE_GAZEBO_MOTORS_MOTORFACTORY_H_ */
