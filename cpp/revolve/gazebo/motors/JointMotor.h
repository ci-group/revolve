/*
 * JointMotor.h
 *
 *  Created on: May 6, 2015
 *      Author: elte
 */

#ifndef REVOLVE_GAZEBO_MOTORS_JOINTMOTOR_H_
#define REVOLVE_GAZEBO_MOTORS_JOINTMOTOR_H_

#include <revolve/gazebo/motors/Motor.h>

namespace revolve {
namespace gazebo {

class JointMotor: public Motor {
public:
	JointMotor(::gazebo::physics::ModelPtr model, std::string partId,
			std::string motorId, sdf::ElementPtr motor, unsigned int outputs);
	virtual ~JointMotor();
protected:
	/**
	 * The joint this motor is controlling
	 */
	::gazebo::physics::JointPtr joint_;

	/**
	 * Scoped name of the controlled joint
	 */
	std::string jointName_;
};

} /* namespace gazebo */
} /* namespace revolve */

#endif /* REVOLVE_GAZEBO_MOTORS_JOINTMOTOR_H_ */
