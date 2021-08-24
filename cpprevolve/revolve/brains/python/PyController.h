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
 * Date: Aug 11, 2021
 *
 */
#ifndef REVOLVE_PYCONTROLLER_H
#define REVOLVE_PYCONTROLLER_H

#include "../controller/Controller.h"
#include "../controller/actuators/Actuator.h"
#include "../controller/sensors/Sensor.h"

class PyController : public ::revolve::Controller {
public:
    PyController() = default;

    ~PyController() override = default;

    void update(
            const std::vector<std::shared_ptr<::revolve::Actuator>> &actuators,
            const std::vector<std::shared_ptr<::revolve::Sensor>> &sensors,
            const double time,
            const double step
    ) override
    {
        PYBIND11_OVERRIDE_PURE(
                void,                        /* Return type */
                ::revolve::Controller,       /* Parent class */
                update,                      /* Name of function in C++ (must match Python name) */
                actuators,sensors,time,step  /* Argument(s) */
                );
    }
};

#endif //REVOLVE_PYCONTROLLER_H
