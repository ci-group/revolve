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
#ifndef REVOLVE_SENSOR_H
#define REVOLVE_SENSOR_H

namespace revolve {

class Sensor
{
public:
    explicit Sensor(unsigned int n_inputs)
        : _n_inputs(n_inputs)
    {}

    /// \brief Read the value of the sensor into the
    /// \param[in] _input: array.
    /// \brief[in,out] _input Input value to write on
    ///
    /// Reads the current value of this sensor into the given
    /// network output array. This should fill the number of input neurons
    /// the sensor specifies to have, i.e. if the sensor specifies 2 input
    /// neurons it should fill `input[0]` and `input[1]`
    virtual void read(double *input) = 0;

    [[nodiscard]] inline unsigned int n_inputs() const {return this->_n_inputs;}

private:
    const unsigned int _n_inputs;
};

}

#endif //REVOLVE_SENSOR_H
