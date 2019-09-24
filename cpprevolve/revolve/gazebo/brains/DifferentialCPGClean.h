//
// Created by andi on 20-09-19.
//

#ifndef REVOLVE_DIFFERENTIALCPGCLEAN_H
#define REVOLVE_DIFFERENTIALCPGCLEAN_H
#include <revolve/brains/controller/actuators/Actuator.h>
#include <revolve/brains/controller/DifferentialCPG.h>
#include <revolve/gazebo/motors/ActuatorWrapper.h>
#include "Brain.h"

namespace revolve
{
    namespace gazebo
    {
        std::vector<std::unique_ptr<revolve::Actuator>> convertMotorsToActuators(const std::vector<MotorPtr> &_motors)
        {
            std::vector<std::unique_ptr<revolve::Actuator>> actuators;
            actuators.reserve(_motors.size());
            for (auto &motor: _motors) {
                actuators.push_back(std::make_unique<ActuatorWrapper>(motor.get(), 0, 0, 0));
            }

            return actuators;
        }

        class DifferentialCPGClean: public Brain, private revolve::DifferentialCPG
        {
        public:
            explicit DifferentialCPGClean(const revolve::DifferentialCPG::ControllerParams &params,
                                          const std::vector< MotorPtr > &_motors)
                    : Brain()
                    , revolve::DifferentialCPG(params, revolve::gazebo::convertMotorsToActuators(_motors))
            {}

            void Update(const std::vector<MotorPtr> &_motors,
                        const std::vector<SensorPtr> &_sensors,
                        const double _time,
                        const double _step) override
            {
                std::vector<std::unique_ptr<revolve::Actuator>> actuators = revolve::gazebo::convertMotorsToActuators(_motors);
                std::vector<std::unique_ptr<revolve::Sensor>> sensors;  // CPG does not actually have any sensors.

                revolve::DifferentialCPG::update(actuators, sensors, _time, _step);
            }
        };
    }
}



#endif //REVOLVE_DIFFERENTIALCPGCLEAN_H
