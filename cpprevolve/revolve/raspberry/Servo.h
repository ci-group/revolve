//
// Created by matteo on 14/06/19.
//

#ifndef REVOLVE_SERVO_H
#define REVOLVE_SERVO_H

#include "PIGPIOConnection.h"

namespace revolve {

class Servo {
public:
    explicit Servo(short pin, unsigned int frequency=50, int range=1000, bool inverse=false);

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

private:
    short pin;
    PIGPIOConnection pigpio;
    float minPWM;
    float maxPWM;
};

}


#endif //REVOLVE_SERVO_H
