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
private:
	MotorFactory();
public:
	virtual ~MotorFactory();

	/**
	 * Creates a motor for the given model for the given SDF element.
	 */
	static MotorPtr create(sdf::ElementPtr motor, ::gazebo::physics::ModelPtr model,
			unsigned int actuationTime);
};

} /* namespace gazebo */
} /* namespace revolve */

#endif /* REVOLVE_GAZEBO_MOTORS_MOTORFACTORY_H_ */
