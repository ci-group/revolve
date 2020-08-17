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
* Created on: May 3, 2015
*
*/

#ifndef REVOLVE_GAZEBO_PLUGIN_ROBOTCONTROLLER_H_
#define REVOLVE_GAZEBO_PLUGIN_ROBOTCONTROLLER_H_

#include <vector>

#include <gazebo/gazebo.hh>
#include <gazebo/physics/physics.hh>
#include <gazebo/common/common.hh>
#include <gazebo/msgs/msgs.hh>

#include <revolve/gazebo/Types.h>

#include <revolve/gazebo/battery/Battery.h>


#include <revolve/msgs/model_inserted.pb.h>
#include <revolve/msgs/robot_states.pb.h>

namespace revolve
{
  namespace gazebo
  {
    class RobotController
            : public ::gazebo::ModelPlugin
    {
      /// \brief Constructor
      public: RobotController();

      /// \brief Destructor
      public: virtual ~RobotController();

      /// \brief Load method
      public: void Load(
              ::gazebo::physics::ModelPtr _parent,
              sdf::ElementPtr _sdf) override;

      /// \return Factory class that creates motors for this model
      public: virtual MotorFactoryPtr MotorFactory(
          ::gazebo::physics::ModelPtr _model);

      /// \return Factory class that creates motors for this robot
      public: virtual SensorFactoryPtr SensorFactory(
          ::gazebo::physics::ModelPtr _model);

      /// \brief Update event which, by default, is called periodically
      /// according to the update rate specified in the robot plugin.
      public: virtual void DoUpdate(const ::gazebo::common::UpdateInfo _info);

      /// \brief Returns the battery level
      /// \details Methods allows reading and writing the battery level in
      /// the robot SDF. This is mostly useful for the `BatterySensor` to
      /// obtain the battery state, and storing it in the SDF also means it
      /// will be adequately backed up in an eventual snapshot.
      public: double BatteryLevel();

      /// \brief Sets the battery level if possible
      public: void SetBatteryLevel(double _level);

      /// \brief Request listener for battery update
      public: void UpdateBattery(ConstRequestPtr &_request);

      /// \brief Detects and loads motors in the plugin spec
      protected: virtual void LoadActuators(const sdf::ElementPtr _sdf);

      /// \brief Detects and loads sensors in the plugin spec.
      protected: virtual void LoadSensors(const sdf::ElementPtr _sdf);

      /// \brief Loads the brain from the `rv:brain` element.
      /// \details By default this tries to construct a `StandardNeuralNetwork`.
      protected: virtual void LoadBrain(const sdf::ElementPtr _sdf);

      /// \brief Loads / initializes the robot battery
      protected: virtual void LoadBattery(const sdf::ElementPtr _sdf);

      protected: virtual void OnBeginUpdate(const ::gazebo::common::UpdateInfo &_info);
      /// \brief Method called at the end of the default `Load` function.
      /// \details This  should be used to initialize robot actuation, i.e.
      /// register some update event. By default, this grabs the
      /// `update_rate` from the robot config pointer, and binds
      protected: virtual void Startup(
              ::gazebo::physics::ModelPtr _parent,
              sdf::ElementPtr _sdf);

      /// \brief Default method bound to world update event, checks whether the
      /// \brief actuation time has passed and updates if required.
      protected: void CheckUpdate(const ::gazebo::common::UpdateInfo _info);

      // Listener for analysis requests
      virtual void HandleRequest(ConstRequestPtr &request);

      /// \brief Networking node
      protected: ::gazebo::transport::NodePtr node_;

      /// \brief Subscriber for battery update request
      protected: ::gazebo::transport::SubscriberPtr batterySetSub_;

      protected: ::gazebo::event::ConnectionPtr onBeginUpdateConnection;

      // Response publisher
      protected: ::gazebo::transport::PublisherPtr responsePub_;

      /// \brief Responder for battery update request
      protected: ::gazebo::transport::PublisherPtr batterySetPub_;

      /// \brief Holds an instance of the motor factory
      protected: MotorFactoryPtr motorFactory_;

      /// \brief Holds an instance of the sensor factory
      protected: SensorFactoryPtr sensorFactory_;

      /// \brief Brain controlling this model
      protected: BrainPtr brain_;

      /// \brief Actuation time, in seconds
      protected: double actuationTime_;

      /// \brief Time of initialisation
      protected: double initTime_;

      /// \brief rv:battery element, if present
      protected: sdf::ElementPtr batteryElem_;

      /// \brief Time of the last actuation, in seconds and nanoseconds
      protected: ::gazebo::common::Time lastActuationTime_;

      /// \brief Motors in this model
      protected: std::vector< MotorPtr > motors_;

      /// \brief Sensors in this model
      protected: std::vector< SensorPtr > sensors_;

      /// \brief Pointer to the model
      protected: ::gazebo::physics::ModelPtr model_;

      /// \brief Pointer to the world
      protected: ::gazebo::physics::WorldPtr world_;

      /// \brief Shared pointer to the battery
      protected: std::shared_ptr<Battery> battery_;

      protected: ::gazebo::physics::Model_V models_to_remove;

      // Request subscriber
      protected: ::gazebo::transport::SubscriberPtr requestSub_;

      // Death sentence list. It collects all the end time for all robots that have
      // a death sentence
      // NEGATIVE DEATH SENTENCES mean total lifetime, death sentence not yet initialized.
      protected: std::map<std::string, double> death_sentences_;

      // Mutex for the deleteMap_
      protected: boost::mutex death_sentences_mutex_;

      // Publisher for periodic robot poses
      protected: ::gazebo::transport::PublisherPtr robotStatesPub_;

      // Frequency at which robot info is published
      // Defaults to 0, which means no update at all
      protected: unsigned int robotStatesPubFreq_;
      // Last (simulation) time robot info was sent
      protected: double lastRobotStatesUpdateTime_;

      /// \brief Driver update event pointer
      private: ::gazebo::event::ConnectionPtr updateConnection_;
    };
  } /* namespace gazebo */
} /* namespace revolve */

#endif /* REVOLVE_GAZEBO_PLUGIN_ROBOTCONTROLLER_H_ */
