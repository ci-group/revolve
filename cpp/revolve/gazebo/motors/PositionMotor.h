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
	// World update event function
//	void OnUpdate(const ::gazebo::common::UpdateInfo info);

	// Perform the actual update given the step size
	void DoUpdate(const ::gazebo::common::Time &simTime);

	// Store update event pointer
	::gazebo::event::ConnectionPtr updateConnection_;

	// Last update time, used to determine update step time
	::gazebo::common::Time prevUpdateTime_;

	// Current position target
	double positionTarget_;

	// Upper and lower position limits
	double lowerLimit_;
	double upperLimit_;

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
