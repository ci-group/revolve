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
 * Date: Jun 14, 2019
 *
 */
#ifndef REVOLVE_CONTROLLER_H
#define REVOLVE_CONTROLLER_H

#include "actuators/Actuator.h"
#include "sensors/Sensor.h"
#include <vector>
#include <memory>

namespace revolve
{

class Controller
{
public:
    /// \brief Constructor
    explicit Controller() = default;

    /// \brief Deconstructor
    virtual ~Controller() = default;

    virtual void update(
            const std::vector<std::shared_ptr<Actuator>> &_actuators,
            const std::vector<std::shared_ptr<Sensor>> &_sensors,
            double _time,
            double _step
    ) = 0;
};

}


#endif //REVOLVE_CONTROLLER_H
