//
// Created by matteo on 14/06/19.
//

#ifndef REVOLVE_PIGPIOCONNECTION_H
#define REVOLVE_PIGPIOCONNECTION_H

extern "C" {
#include "pigpiod_if2.h"
}

#include <exception>
#include <stdexcept>

class PIGPIOConnection {
public:
    explicit PIGPIOConnection(const char* address= nullptr, const char* port= nullptr) {
        this->connection = pigpio_start(address, port);
        if (this->connection < 0) {
            throw std::runtime_error("connection unsuccessful");
        }
    }

    ~PIGPIOConnection() {
        pigpio_stop(connection);
    }

    int set_pwm_frequency(unsigned user_gpio, unsigned frequency) {
        return set_PWM_frequency(connection, user_gpio, frequency);
    }

    int set_pwm_range(unsigned user_gpio, unsigned range) {
        return set_PWM_range(connection, user_gpio, range);
    }

    int set_pwm_dutycycle(unsigned user_gpio, unsigned dutycycle) {
        return set_PWM_dutycycle(connection, user_gpio, dutycycle);
    }

private:
    int connection;
};


#endif //REVOLVE_PIGPIOCONNECTION_H
