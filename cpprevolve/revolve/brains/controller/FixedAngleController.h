//
// Created by Matteo De Carlo on 11/09/2019.
//

#ifndef REVOLVE_FIXEDANGLECONTROLLER_H
#define REVOLVE_FIXEDANGLECONTROLLER_H

#include "Controller.h"

namespace revolve
{

class FixedAngleController: public Controller
{
public:
    explicit FixedAngleController(double angle)
        : angle(angle)
    {}

    void update(const std::vector<std::shared_ptr<Actuator> > &_actuators,
                const std::vector<std::shared_ptr<Sensor> > &_sensors,
                const double _time,
                const double _step) override
    {
        std::vector<double> output(1, angle);
        for (auto &actuator: _actuators) {
            output.resize(actuator->n_outputs(), angle);
            actuator->write(output.data(), _step);
        }
    }

private:
    double angle;
};

}


#endif //REVOLVE_FIXEDANGLECONTROLLER_H
