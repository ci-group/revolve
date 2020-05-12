//
// Created by matteo on 14/06/19.
//

#include "Servo.h"
#include "PIGPIOConnection.h"

using namespace revolve::raspberry;

#define POSITION_OFF 0
#define POSITION_BEGIN 40
#define POSITION_MIDDLE 75
#define POSITION_END 110

Servo::Servo(double coordinate_x, double coordinate_y, double coordinate_z, PIGPIOConnection *connection, unsigned short pin, unsigned int frequency, int range, bool inverse)
    : Actuator(1, coordinate_x, coordinate_y, coordinate_z)
    , pin(pin)
    , pigpio(connection)
    , frequency(frequency)
    , range(range)
    , inverse(inverse)
{
    pigpio->set_pwm_frequency(pin, frequency);
    pigpio->set_pwm_range(pin, range);

    if (inverse) {
        minPWM = POSITION_END;
        maxPWM = POSITION_BEGIN;
    } else {
        minPWM = POSITION_BEGIN;
        maxPWM = POSITION_END;
    }
}

void Servo::move_to_position(double position)
{
    if (position < -1.0)
        position = -1.0;
    else if (position > 1.0)
        position = 1.0;

    position *= 0.7;

    position = this->minPWM + (1 + position) * (this->maxPWM - this->minPWM) / 2;

    this->pigpio->set_pwm_dutycycle(this->pin, static_cast<unsigned>(position));
}

void Servo::off()
{
    this->pigpio->set_pwm_dutycycle(this->pin, POSITION_OFF);
}

void Servo::write(const double *output_vector, double step)
{
    double output = output_vector[0];
    this->move_to_position(output);
}

std::ostream &operator<<(std::ostream &os, Servo const &s) {
    return s.print(os);
}
