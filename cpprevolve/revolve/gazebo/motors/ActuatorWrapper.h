//
// Created by Matteo De Carlo on 11/09/2019.
//

#ifndef REVOLVE_ACTUATORWRAPPER_H
#define REVOLVE_ACTUATORWRAPPER_H


#include <revolve/brains/controller/actuators/Actuator.h>
#include "Motor.h"

namespace revolve
{
    namespace gazebo
    {

        class ActuatorWrapper: public revolve::Actuator
        {
        public:
            explicit ActuatorWrapper(Motor *wrapped_actuator, double x, double y, double z)
                    : revolve::Actuator(wrapped_actuator->Outputs(), x, y, z)
                    , wrapped_actuator(wrapped_actuator)
            {
                assert(wrapped_actuator);
            }

            void write(const double *output, double step) override
            {
                wrapped_actuator->Update(output, step);
            }

        private:
            Motor *wrapped_actuator;
        };

    }
}


#endif //REVOLVE_ACTUATORWRAPPER_H