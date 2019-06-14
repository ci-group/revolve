//
// Created by matteo on 14/06/19.
//

#include "Servo.h"
#include "PIGPIOConnection.h"

using namespace revolve;

#define POSITION_OFF 0
#define POSITION_BEGIN 40
#define POSITION_MIDDLE 75
#define POSITION_END 110

Servo::Servo(short pin, unsigned int frequency, int range, bool inverse)
    : pin(pin)
    , pigpio()
{
    pigpio.set_pwm_frequency(pin, frequency);
    pigpio.set_pwm_range(pin, range);

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

    this->pigpio.set_pwm_dutycycle(this->pin, static_cast<unsigned>(position));
}

void Servo::off()
{
    this->pigpio.set_pwm_dutycycle(this->pin, 0);
}
