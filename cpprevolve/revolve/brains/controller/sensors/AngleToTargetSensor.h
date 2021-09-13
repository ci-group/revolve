//
// Created by Matteo De Carlo on 25/02/2020.
//

#ifndef REVOLVE_ANGLETOTARGETSENSOR_H
#define REVOLVE_ANGLETOTARGETSENSOR_H

#include "Sensor.h"

namespace revolve
{

class AngleToTargetSensor : public Sensor {
public:
    explicit AngleToTargetSensor()
        : Sensor(1)
    {}

    virtual double angle_to_target() = 0;

    void read(double *input) override
    {
        *input = angle_to_target();
    }
};

}

#endif //REVOLVE_ANGLETOTARGETSENSOR_H
