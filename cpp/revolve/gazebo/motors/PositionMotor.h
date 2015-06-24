/**
 * Position based (servo) motor
 */

#ifndef REVOLVE_GAZEBO_POSITIONMOTOR_H_
#define REVOLVE_GAZEBO_POSITIONMOTOR_H_

#include <revolve/gazebo/motors/JointMotor.h>

#include <gazebo/common/common.hh>

namespace revolve {
namespace gazebo {

class PositionMotor : public JointMotor {
public:
	/**
	 * @param The model the motor is contained in
	 * @param The joint driven by the motor
	 * @param The part ID the motor belongs to
	 * @param Whether the motor is velocity driven (the alternative is position driven)
	 * @param The derivative gain of the motor's PID controller
	 */
	PositionMotor(::gazebo::physics::ModelPtr model, std::string partId,
				  std::string motorId, sdf::ElementPtr motor);
	virtual ~PositionMotor();

	virtual void update(double * outputs, double step);

protected:
	// Upper and lower position limits
	double lowerLimit_;
	double upperLimit_;

	// Velocity limits. For the position motor these may be used
	// to prevent unstable behavior by not applying any force when
	// the current velocity exceeds these values.
	double minVelocity_;
	double maxVelocity_;

	// Whether this joint can achieve a full range of motion, meaning
	// it can flip from a positive to a negative angle. This is set
	// to true whenever the total range is >/ 2 pi.
	bool fullRange_;

	// Motor noise
	double noise_;

	// PID that controls this motor
	::gazebo::common::PID pid_;
};

} /* namespace gazebo */
} /* namespace revolve */

#endif /* REVOLVE_GAZEBO_POSITIONMOTOR_H_ */
