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

#pragma once

#include <vector>

#include <gazebo/gazebo.hh>
#include <gazebo/physics/physics.hh>
#include <gazebo/common/common.hh>
#include <gazebo/msgs/msgs.hh>

#include <revolve/gazebo/Types.h>
#include <revolve/brains/learner/Learner.h>
#include "revolve/brains/controller/sensors/Sensor.h"
#include "revolve/brains/controller/actuators/Actuator.h"
#include <revolve/gazebo/brains/GazeboReporter.h>

#include "revolve/brains/learner/NIPES.h"
#include "revolve/brains/learner/DifferentialEvo.h"

namespace revolve {
namespace gazebo {

class RobotController : public ::gazebo::ModelPlugin
{
public:
    /// \brief Constructor
    RobotController();

    /// \brief Destructor
    virtual ~RobotController();

    /// \brief Load method
    void Load(
            ::gazebo::physics::ModelPtr _parent,
            sdf::ElementPtr _sdf) override;

    /// \return Factory class that creates motors for this model
    virtual MotorFactoryPtr MotorFactory(
            ::gazebo::physics::ModelPtr _model);

    /// \return Factory class that creates motors for this robot
    virtual SensorFactoryPtr SensorFactory(
            ::gazebo::physics::ModelPtr _model);

    /// \brief Update event which, by default, is called periodically
    /// according to the update rate specified in the robot plugin.
    virtual void DoUpdate(const ::gazebo::common::UpdateInfo _info);

    /// \brief Returns the battery level
    /// \details Methods allows reading and writing the battery level in
    /// the robot SDF. This is mostly useful for the `BatterySensor` to
    /// obtain the battery state, and storing it in the SDF also means it
    /// will be adequately backed up in an eventual snapshot.
    double BatteryLevel();

    /// \brief Sets the battery level if possible
    void SetBatteryLevel(double _level);

    /// \brief Request listener for battery update
    void UpdateBattery(ConstRequestPtr &_request);

    /// \brief Detects and loads motors in the plugin spec
protected:
    virtual void LoadActuators(const sdf::ElementPtr _sdf);

    /// \brief Detects and loads sensors in the plugin spec.
    virtual void LoadSensors(const sdf::ElementPtr _sdf);

    /// \brief Loads the brain from the `rv:brain` element.
    /// \details By default this tries to construct a `StandardNeuralNetwork`.
    virtual void LoadBrain(const sdf::ElementPtr _sdf);

    /// \brief Loads / initializes the robot battery
    virtual void LoadBattery(const sdf::ElementPtr _sdf);

    /// \brief Method called at the end of the default `Load` function.
    /// \details This  should be used to initialize robot actuation, i.e.
    /// register some update event. By default, this grabs the
    /// `update_rate` from the robot config pointer, and binds
    virtual void Startup(
            ::gazebo::physics::ModelPtr _parent,
            sdf::ElementPtr _sdf);

    /// \brief Default method bound to world update event, checks whether the
    /// \brief actuation time has passed and updates if required.
    void CheckUpdate(const ::gazebo::common::UpdateInfo _info);

protected:
    std::unique_ptr<::revolve::gazebo::Evaluator> evaluator;
    std::unique_ptr<::revolve::EvaluationReporter> reporter;
    std::shared_ptr<::revolve::gazebo::GazeboReporter> gazebo_reporter;

    /// \brief Networking node
    ::gazebo::transport::NodePtr node_;

    /// \brief Subscriber for battery update request
    ::gazebo::transport::SubscriberPtr batterySetSub_;

    /// \brief Responder for battery update request
    ::gazebo::transport::PublisherPtr batterySetPub_;

    /// \brief Holds an instance of the motor factory
    MotorFactoryPtr motorFactory_;

    /// \brief Holds an instance of the sensor factory
    SensorFactoryPtr sensorFactory_;

    /// \brief Learner for the brain controlling this model
    std::unique_ptr<::revolve::Learner> learner;

    /// \brief Actuation time, in seconds
    double actuationTime_;

    /// \brief Time of initialisation
    ::gazebo::common::Time initTime_;

    /// \brief rv:battery element, if present
    sdf::ElementPtr batteryElem_;

    /// \brief Time of the last actuation, in seconds and nanoseconds
    ::gazebo::common::Time lastActuationTime_;

    /// \brief Motors in this model
    std::vector<MotorPtr> motors_;

    /// \brief Sensors in this model
    std::vector<SensorPtr> sensors_;

    /// \brief Pointer to the model
    ::gazebo::physics::ModelPtr model_;

    /// \brief Pointer to the world
    ::gazebo::physics::WorldPtr world_;

    /// \brief Driver update event pointer
private:
    ::gazebo::event::ConnectionPtr updateConnection_;
};

} /* namespace gazebo */
} /* namespace revolve */
