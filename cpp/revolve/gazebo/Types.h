#ifndef REVOLVE_GZ_MODEL_TYPES_H_
#define REVOLVE_GZ_MODEL_TYPES_H_

#include <boost/shared_ptr.hpp>

namespace revolve {
namespace gazebo {
	class Motor;
	class VirtualSensor;
	class Brain;
	class MotorFactory;
	class SensorFactory;

	typedef boost::shared_ptr< Brain > BrainPtr;
	typedef boost::shared_ptr< Motor > MotorPtr;
	typedef boost::shared_ptr< VirtualSensor > SensorPtr;
	typedef boost::shared_ptr< MotorFactory > MotorFactoryPtr;
	typedef boost::shared_ptr< SensorFactory > SensorFactoryPtr;
}
}

#endif
