/*
* Copyright (C) 2017 Vrije Universiteit Amsterdam
*
* Licensed under the Apache License, Version 2.0 (the "License");
* You may obtain a copy of the License at
*
*     http://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
*
* Description: TODO: <Add brief description about file purpose>
* Author: Elte Hupkes
*
*/

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
   * @return Factory class that creates motors for this model
   */
  virtual MotorFactoryPtr getMotorFactory(::gazebo::physics::ModelPtr model);

  /**
   * @return Factory class that creates motors for this robot
   */
  virtual SensorFactoryPtr getSensorFactory(::gazebo::physics::ModelPtr model);

  /**
   * Update event which, by default, is called periodically according to the
   * update rate specified in the robot plugin.
   */
  virtual void DoUpdate(const ::gazebo::common::UpdateInfo info);

  // Methods below allow reading and writing the battery level
  // in the robot SDF. This is mostly useful for the `BatterySensor`
  // to obtain the battery state, and storing it in the SDF also
  // means it will be adequately backed up in an eventual snapshot.
  /**
   * Returns the battery level
   */
  double GetBatteryLevel();

  /**
   * Sets the battery level if possible
   */
  void SetBatteryLevel(double level);

  /**
   * Request listener for battery update
   */
  void UpdateBattery(ConstRequestPtr & request);
  protected:
  /**
   * Detects and loads motors in the plugin spec
   */
  virtual void LoadMotors(sdf::ElementPtr sdf);

  /**
   * Detects and loads sensors in the plugin spec.
   */
  virtual void LoadSensors(sdf::ElementPtr sdf);

  /**
   * Loads the brain from the `rv:brain` element. By default this
   * tries to construct a `StandardNeuralNetwork`.
   */
  virtual void LoadBrain(sdf::ElementPtr sdf);

  /**
   * Loads / initializes the robot battery
   */
  virtual void LoadBattery(sdf::ElementPtr sdf);

  /**
   * Method that is called at the end of the default `Load` function. This
   * should be used to initialize robot actuation, i.e. register some update
   * event. By default, this grabs the `update_rate` from the robot config
   * pointer, and binds
   */
  virtual void startup(::gazebo::physics::ModelPtr _parent, sdf::ElementPtr _sdf);

  /**
   * Default method bound to world update event, checks whether the
   * actuation time has passed and updates if required.
   */
  void CheckUpdate(const ::gazebo::common::UpdateInfo info);

  /**
   * Networking node
   */
  ::gazebo::transport::NodePtr node_;

  /**
   * Subscriber/responder for battery update request
   */
  ::gazebo::transport::SubscriberPtr batterySetSub_;
  ::gazebo::transport::PublisherPtr batterySetPub_;

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
   * Actuation time, in seconds
   */
  double actuationTime_;

  // Time of initialisation
  double initTime_;

  // rv:battery element, if present
  sdf::ElementPtr batteryElem_;

  /**
   * Time of the last actuation, in
   * seconds and nanoseconds
   */
  ::gazebo::common::Time lastActuationTime_;

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

  private:
    // Driver update event pointer
    ::gazebo::event::ConnectionPtr updateConnection_;
};

} /* namespace gazebo */
} /* namespace revolve */

#endif /* REVOLVE_GAZEBO_PLUGIN_ROBOTCONTROLLER_H_ */
