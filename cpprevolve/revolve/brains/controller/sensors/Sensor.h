//
// Created by matteo on 14/06/19.
//

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

    inline unsigned int n_inputs() const {return this->_n_inputs;}

private:
    const unsigned int _n_inputs;
};

}

#endif //REVOLVE_SENSOR_H
