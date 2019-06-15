//
// Created by matteo on 14/06/19.
//

#ifndef REVOLVE_SERVO_H
#define REVOLVE_SERVO_H

#include "PIGPIOConnection.h"
#include "../brains/controller/actuators/Actuator.h"
#include <iostream>

namespace revolve {

class Servo
    : public Actuator
{
public:
    explicit Servo(
            double coordinate_x,
            double coordinate_y,
            double coordinate_z,
            PIGPIOConnection *connection,
            unsigned short pin,
            unsigned int frequency=50,
            int range=1000,
            bool inverse=false
    );

    ~Servo() {
        this->off();
    }

    /***
     * Sends signal to the engine to move to a specified position.
     * Position should be in range [-1, 1] with 0 being the middle.
     * @param position
     */
    void move_to_position(double position);

    void center() { move_to_position(0); }

    void off();

    virtual void write(const double *output, double step) override;

    std::ostream &print(std::ostream &os) const
    {
        os << "Servo pin:\t" << this->pin << std::endl;
        os << "\tcoordinates [" << this->coordinate_x() << ',' << this->coordinate_y() << ',' << this->coordinate_z() << ']' << std::endl;
        os << "\tfrequency:\t" << this->frequency << std::endl;
        os << "\trange:    \t" << this->range << std::endl;
        os << "\tinverse:  \t" << this->inverse;

        return os;
    }

private:
    unsigned short pin;
    PIGPIOConnection *pigpio;
    unsigned int frequency;
    int range;
    bool inverse;
    float minPWM;
    float maxPWM;
};

}

std::ostream &operator<<(std::ostream &os, revolve::Servo const &s);

#endif //REVOLVE_SERVO_H
