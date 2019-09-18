//
// Created by Matteo De Carlo on 11/09/2019.
//

#ifndef GAZEBO_REVOLVE_FIXEDANGLECONTROLLER_H
#define GAZEBO_REVOLVE_FIXEDANGLECONTROLLER_H


#include <revolve/brains/controller/actuators/Actuator.h>
#include <revolve/brains/controller/sensors/Sensor.h>
#include <revolve/brains/controller/FixedAngleController.h>
#include <revolve/gazebo/motors/ActuatorWrapper.h>
#include "Brain.h"

namespace revolve
{
namespace gazebo
{

class FixedAngleController: public Brain, private revolve::FixedAngleController
{
public:
    explicit FixedAngleController(double angle)
        : Brain()
        , revolve::FixedAngleController(angle)
    {}

    void Update(const std::vector<MotorPtr> &_motors,
                const std::vector<SensorPtr> &_sensors,
                const double _time,
                const double _step) override
    {
        std::vector<std::unique_ptr<revolve::Actuator>> actuators;
        std::vector<std::unique_ptr<revolve::Sensor>> sensors;
        actuators.reserve(_motors.size());
        for (auto &motor: _motors) {
            actuators.push_back(std::make_unique<ActuatorWrapper>(motor.get(), 0, 0, 0));
        }
        revolve::FixedAngleController::update(actuators, sensors, _time, _step);
    }
};

}
}


#endif //GAZEBO_REVOLVE_FIXEDANGLECONTROLLER_H
