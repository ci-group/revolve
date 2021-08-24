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
#ifndef REVOLVE_ACTUATOR_H
#define REVOLVE_ACTUATOR_H

#include <tuple>

namespace revolve {

class Actuator
{
public:
    explicit Actuator(unsigned int n_outputs, double x, double y, double z)
            : Actuator(n_outputs, {x,y,z})
    {}
    explicit Actuator(unsigned int n_outputs, const std::tuple<double, double, double> coordinates)
            : _n_outputs(n_outputs)
            , coordinates(coordinates)
    {}

    [[nodiscard]] inline double coordinate_x() const { return std::get<0>(this->coordinates); }
    [[nodiscard]] inline double coordinate_y() const { return std::get<1>(this->coordinates); }
    [[nodiscard]] inline double coordinate_z() const { return std::get<2>(this->coordinates); }

    virtual void write(const double *output, double step) = 0;

    [[nodiscard]] inline unsigned int n_outputs() const {return this->_n_outputs;}

protected:
    const unsigned int _n_outputs;
    std::tuple<double, double, double> coordinates;
};

}


#endif //REVOLVE_ACTUATOR_H
