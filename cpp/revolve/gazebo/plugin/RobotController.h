/*
 * ModelController.h
 *
 *  Created on: May 3, 2015
 *      Author: elte
 */

#ifndef REVOLVE_GAZEBO_PLUGIN_ROBOTCONTROLLER_H_
#define REVOLVE_GAZEBO_PLUGIN_ROBOTCONTROLLER_H_

#include <gazebo/gazebo.hh>
#include <gazebo/physics/physics.hh>
#include <gazebo/common/common.hh>
#include <gazebo/msgs/msgs.hh>

#include <revolve/gazebo/Types.h>

#include <vector>

namespace revolve {
namespace gazebo {

class RobotController: public ::gazebo::ModelPlugin {
public:
	RobotController();
	virtual ~RobotController();

public:
	virtual void Load(::gazebo::physics::ModelPtr _parent, sdf::ElementPtr _sdf);

	/**
	 * Called when the driver sensor updates
	 */
//	void OnUpdate();

	/**
	 * @return Factory class that creates motors for this model
	 */
	virtual MotorFactoryPtr getMotorFactory(::gazebo::physics::ModelPtr model);

	/**
	 * @return Factory class that creates motors for this robot
	 */
	virtual SensorFactoryPtr getSensorFactory(::gazebo::physics::ModelPtr model);
protected:
	/**
	 * Detects and loads motors in the plugin spec
	 */
	virtual void loadMotors(sdf::ElementPtr sdf);

	/**
	 * Detects and loads sensors in the plugin spec.
	 */
	virtual void loadSensors(sdf::ElementPtr sdf);

	/**
	 * Loads the brain from the `rv:brain` element. By default this
	 * tries to construct a `StandardNeuralNetwork`.
	 */
	virtual void loadBrain(sdf::ElementPtr sdf);

	/**
	 * Holds an instance of the motor factory
	 */
	MotorFactoryPtr motorFactory_;

	/**
	 * Holds an instance of the sensor factory
	 */
	SensorFactoryPtr sensorFactory_;

	/**
	 * Brain controlling this model
	 */
	BrainPtr brain_;

	/**
	 * Actuation time, in nanoseconds
	 */
	unsigned int actuationTime_;

	/**
	 * Time of the last actuation, in
	 * seconds and nanoseconds
	 */
	unsigned int lastActuationSec_;
	unsigned int lastActuationNsec_;

	/**
	 * Motors in this model
	 */
	std::vector< MotorPtr > motors_;

	/**
	 * Sensors in this model
	 */
	std::vector< SensorPtr > sensors_;

    // Pointer to the model
    ::gazebo::physics::ModelPtr model;

    // Pointer to the world
	::gazebo::physics::WorldPtr world;

    // Pointer to the driver sensor
    SensorPtr driver;
private:
    // Driver update event pointer
    ::gazebo::event::ConnectionPtr updateConnection_;
};

} /* namespace gazebo */
} /* namespace revolve */

#endif /* REVOLVE_GAZEBO_PLUGIN_ROBOTCONTROLLER_H_ */
