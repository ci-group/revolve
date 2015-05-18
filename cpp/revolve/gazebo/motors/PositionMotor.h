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
	PositionMotor(::gazebo::physics::ModelPtr model, std::string partId, std::string motorId, sdf::ElementPtr motor);
	virtual ~PositionMotor();

	virtual void update(double * outputs, unsigned int step);

protected:
	// Upper and lower position limits
	double lowerLimit_;
	double upperLimit_;

	// Motor noise
	double noise_;

	/**
	 * The joint controller of the attaching model
	 */
	::gazebo::physics::JointControllerPtr jointController_;
};

} /* namespace gazebo */
} /* namespace revolve */

#endif /* REVOLVE_GAZEBO_POSITIONMOTOR_H_ */
