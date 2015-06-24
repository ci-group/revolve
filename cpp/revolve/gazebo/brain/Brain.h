/*
 * Specifies a utility `Brain` base class. If your brain doesn't
 * fit this model, something else can easily be used by simply
 * ignoring the default brain behavior in the `RobotController`.
 */

#ifndef REVOLVE_GAZEBO_BRAIN_BRAIN_H_
#define REVOLVE_GAZEBO_BRAIN_BRAIN_H_

#include <revolve/gazebo/Types.h>
#include <boost/shared_ptr.hpp>
#include <gazebo/common/common.hh>

namespace revolve {
namespace gazebo {

class Brain {
public:
	Brain() {};
	virtual ~Brain() {};

	/**
	 * Update step called for the brain.
	 *
	 * @param List of motors
	 * @param List of sensors
	 * @param Current simulation time
	 * @param Actuation step size in seconds
	 */
	virtual void update(const std::vector< MotorPtr > & motors, const std::vector< SensorPtr > & sensors,
				double t, double step) = 0;
};

} /* namespace gazebo */
} /* namespace revolve */

#endif /* REVOLVE_GAZEBO_BRAIN_BRAIN_H_ */
