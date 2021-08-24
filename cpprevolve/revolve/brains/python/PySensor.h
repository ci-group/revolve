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
#ifndef REVOLVE_PYSENSOR_H
#define REVOLVE_PYSENSOR_H

#include "../controller/sensors/Sensor.h"

class PySensor: public ::revolve::Sensor
{
public:
    explicit PySensor(unsigned int n_inputs)
        : ::revolve::Sensor(n_inputs)
    {}

    void read(double *input) override
    {
        PYBIND11_OVERRIDE_PURE(
                void,            /* Return type */
                revolve::Sensor, /* Parent class */
                read,            /* Name of function in C++ (must match Python name) */
                input            /* Argument(s) */
                );
    }
};

#endif //REVOLVE_PYSENSOR_H
