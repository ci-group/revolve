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
            explicit DifferentialCPGClean(const sdf::ElementPtr cpgParams_sdf,
                                          const std::vector< MotorPtr > &_motors)
                    : Brain()
                    , revolve::DifferentialCPG(DifferentialCPGClean::LoadParamsFromSDF(cpgParams_sdf),
                                                revolve::gazebo::convertMotorsToActuators(_motors))
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

        private:
            static revolve::DifferentialCPG::ControllerParams LoadParamsFromSDF(sdf::ElementPtr controller_sdf)
            {
                // TODO: Add exception handling
                revolve::DifferentialCPG::ControllerParams params;
                params.reset_neuron_random = (controller_sdf->GetAttribute("reset_neuron_random")->GetAsString() == "true");
                params.use_frame_of_reference = (controller_sdf->GetAttribute("use_frame_of_reference")->GetAsString() == "true");
                params.init_neuron_state = stod(controller_sdf->GetAttribute("init_neuron_state")->GetAsString());
                params.range_ub = stod(controller_sdf->GetAttribute("range_ub")->GetAsString());
                params.signal_factor_all = stod(controller_sdf->GetAttribute("signal_factor_all")->GetAsString());
                params.signal_factor_mid = stod(controller_sdf->GetAttribute("signal_factor_mid")->GetAsString());
                params.signal_factor_left_right = stod(controller_sdf->GetAttribute("signal_factor_left_right")->GetAsString());
                params.abs_output_bound = stod(controller_sdf->GetAttribute("abs_output_bound")->GetAsString());

                // Get the weights from the sdf:
                std::string sdf_weights = controller_sdf->GetAttribute("weights")->GetAsString();
                std::string delimiter = ";";

                size_t pos = 0;
                std::string token;
                while ((pos = sdf_weights.find(delimiter)) != std::string::npos) {
                    token = sdf_weights.substr(0, pos);
                    params.weights.push_back(stod(token));
                    sdf_weights.erase(0, pos + delimiter.length());
                }

                return params;
            }

        };
    }
}



#endif //REVOLVE_DIFFERENTIALCPGCLEAN_H
