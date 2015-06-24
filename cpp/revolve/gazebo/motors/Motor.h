/*
 * Motor base class
 */

#ifndef REVOLVE_GAZEBO_MOTORS_MOTOR_H_
#define REVOLVE_GAZEBO_MOTORS_MOTOR_H_

#include <string>

#include <gazebo/gazebo.hh>
#include <gazebo/physics/physics.hh>

#include <revolve/gazebo/Types.h>

namespace revolve {
namespace gazebo {

class Motor {
public:
	Motor(::gazebo::physics::ModelPtr model, std::string partId, std::string motorId, unsigned int outputs);
	virtual ~Motor();

	/**
	 * Updates the motor based on the attached output
	 * of the neural network.
	 *
	 * @param Raw motor update value(s), it is up to the motor to decide how to interpret this.
	 * 		  This is a pointer to an array of values, out of which the motor should read the
	 * 		  first `n` values if it specifies `n` outputs.
	 * @param Actuation time in seconds
	 */
	virtual void update(double * output, double step) = 0;

	/**
	 * @return The part ID
	 */
	std::string partId();

	/**
	 * @return The full ID of the motor (should be unique in the robot)
	 */
	std::string motorId();

	/**
	 * @return Number of output neurons connected to this motor
	 */
	unsigned int outputs();

	/**
	 * @param Pointer to the rv:pid element
	 * @return Gazebo PID
	 */
	static ::gazebo::common::PID createPid(sdf::ElementPtr pid);

protected:
	/**
	 * The model this motor is part of
	 */
	::gazebo::physics::ModelPtr model_;

	/**
	 * ID of the body part the motor belongs to
	 */
	std::string partId_;

	/**
	 * Robot-wide unique motor ID
	 */
	std::string motorId_;

	/**
	 * Number of output neurons that should be connected
	 * to this motor.
	 */
	unsigned int outputs_;
};

} /* namespace gazebo */
} /* namespace tol_robogen */

#endif /* TOL_ROBOGEN_GAZEBO_MOTORS_MOTOR_H_ */
