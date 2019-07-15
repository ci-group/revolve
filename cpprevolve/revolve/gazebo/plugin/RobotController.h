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

      /// \brief Detects and loads motors in the plugin spec
      protected: virtual void LoadActuators(const sdf::ElementPtr _sdf);

      /// \brief Detects and loads sensors in the plugin spec.
      protected: virtual void LoadSensors(const sdf::ElementPtr _sdf);

      /// \brief Loads the brain from the `rv:brain` element.
      /// \details By default this tries to construct a `StandardNeuralNetwork`.
      protected: virtual void LoadBrain(const sdf::ElementPtr _sdf);

      /// \brief Loads / initializes the robot battery
      protected: virtual void LoadBattery(const sdf::ElementPtr _sdf);

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

      /// \brief Networking node
      protected: ::gazebo::transport::NodePtr node_;

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
      protected: std::shared_ptr<::revolve::gazebo::Battery> battery_;

      /// \brief Driver update event pointer
      private: ::gazebo::event::ConnectionPtr updateConnection_;
    };
  } /* namespace gazebo */
} /* namespace revolve */

#endif /* REVOLVE_GAZEBO_PLUGIN_ROBOTCONTROLLER_H_ */
