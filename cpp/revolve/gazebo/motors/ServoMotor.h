/*
 * ServoMotor.h
 *
 *  Created on: Mar 5, 2015
 *      Author: elte
 */

#ifndef REVOLVE_GAZEBO_MOTORS_SERVOMOTOR_H_
#define REVOLVE_GAZEBO_MOTORS_SERVOMOTOR_H_

#include <revolve/gazebo/motors/JointMotor.h>

#include <gazebo/common/common.hh>

namespace revolve {
namespace gazebo {

class ServoMotor: public JointMotor {
public:
	/**
	 * @param The model the motor is contained in
	 * @param The joint driven by the motor
	 * @param The part ID the motor belongs to
	 * @param Whether the motor is velocity driven (the alternative is position driven)
	 * @param The derivative gain of the motor's PID controller
	 */
	ServoMotor(::gazebo::physics::ModelPtr model, std::string partId, sdf::ElementPtr motor);
	virtual ~ServoMotor();

	virtual void update(double * outputs, unsigned int step);

protected:
	// Uper and lower position limits
	double lowerLimit_;
	double upperLimit_;

	// Velocity limits
	double minVelocity_;
	double maxVelocity_;
	bool velocityDriven_;

	// Motor noise
	double noise_;

	/**
	 * The joint controller of the attaching model
	 */
	::gazebo::physics::JointControllerPtr jointController_;

	/**
	 * Store string joint name for repeated use
	 */
	std::string jointName_;
};

} /* namespace gazebo */
} /* namespace revolve */

#endif /* REVOLVE_GAZEBO_MOTORS_SERVOMOTOR_H_ */
