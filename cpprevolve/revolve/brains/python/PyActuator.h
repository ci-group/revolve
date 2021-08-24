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
 * Date: Aug 2, 2021
 *
 */
#ifndef REVOLVE_PYACTUATOR_H
#define REVOLVE_PYACTUATOR_H

#include "../controller/actuators/Actuator.h"
#include <pybind11/pybind11.h>

class PyActuator: public ::revolve::Actuator
{
public:
    explicit PyActuator(unsigned int n_outputs, double x, double y, double z)
        : Actuator(n_outputs, x, y, z)
    {}

    explicit PyActuator(unsigned int n_outputs, const std::tuple<double, double, double> coordinates)
        : Actuator(n_outputs, coordinates)
    {}

    void write(const double *output, double step) override {
        PYBIND11_OVERRIDE_PURE(
                void,                 /* Return type */
                ::revolve::Actuator,  /* Parent class */
                write,                /* Name of function in C++ (must match Python name) */
                output,step           /* Argument(s) */
                );
    }

};


#endif //REVOLVE_PYACTUATOR_H
