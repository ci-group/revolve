/*
 * Copyright (C) 2015-2021 Vrije Universiteit Amsterdam
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
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
 * Author: Matteo De Carlo
 * Date: Sep 11, 2019
 *
 */
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
