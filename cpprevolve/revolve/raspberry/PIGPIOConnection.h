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
#include <sstream>

class PIGPIOConnection {
public:
    explicit PIGPIOConnection(
            const std::string &address = PI_DEFAULT_SOCKET_ADDR_STR,
            unsigned short port = PI_DEFAULT_SOCKET_PORT)
    {
        std::stringstream port_str; port_str << port;
        this->connection = pigpio_start(address.c_str(), port_str.str().c_str());
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
