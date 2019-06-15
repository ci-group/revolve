//
// Created by matteo on 14/06/19.
//

#include "RaspController.h"
#include "Servo.h"
#include <memory>
#include <iostream>
#include <yaml-cpp/yaml.h>

typedef std::unique_ptr<revolve::Servo> Servo_p;

std::vector<Servo_p> read_conf(PIGPIOConnection &pigpio, const YAML::Node &yaml_servos);
void reset(std::vector<Servo_p> &servos);
void center(std::vector<Servo_p> &servos);
void control(std::vector<Servo_p> &servos);


int main( int argc, const char* argv[] )
{
    YAML::Node config = YAML::LoadFile("robot_conf.yaml");

    std::string ip = PI_DEFAULT_SOCKET_ADDR_STR;
    unsigned short port = PI_DEFAULT_SOCKET_PORT;

    try {
        YAML::Node pigpio_address = config["robot_address"];
        ip = pigpio_address["ip"].as<std::string>(PI_DEFAULT_SOCKET_ADDR_STR);
        port = pigpio_address["port"].as<unsigned short>(PI_DEFAULT_SOCKET_PORT);
    } catch (const YAML::RepresentationException &e) {
        // pass
    }
    std::cout << "Connecting to PIGPIO " << ip << ':' << port << std::endl;
    PIGPIOConnection pigpio(ip, port);
    YAML::Node yaml_servos = config["servos"];
    std::vector<Servo_p> servos = read_conf(pigpio, yaml_servos);


    if (argc >= 2 and (std::string(argv[1]) == "reset"))
    {
        std::string command = std::string(argv[1]);
        if (command == "reset")
            reset(servos);
        else if (command == "center")
            center(servos);
        else if (command == "controller")
            control(servos);
        else
            std::clog << "Command \"" << command << "\" not recognized" << std::endl;
    }
    else
    {
        control(servos);
    }
}

std::vector<Servo_p> read_conf(PIGPIOConnection &pigpio, const YAML::Node &yaml_servos)
{
    std::vector<Servo_p> servos;
    for (const YAML::Node &yaml_servo: yaml_servos) {
        unsigned short pin;
        try {
            pin = yaml_servo["pin"].as<unsigned short>();
        } catch (const YAML::InvalidNode &e) {
            std::clog << "Error, pin not setted for one servo" << std::endl;
            std::exit(2);
        }

        double x = 0.0;
        double y = 0.0;
        double z = 0.0;
        try {
            YAML::Node coordinates = yaml_servo["coordinates"];
            x = coordinates[0].as<double>(0.0);
            y = coordinates[1].as<double>(0.0);
            z = coordinates[2].as<double>(0.0);
        } catch (const YAML::InvalidNode &e) {
            // keep default [0,0,0]
        }
        auto frequency = yaml_servo["frequency"].as<unsigned>(50);
        auto range     = yaml_servo["range"]    .as<int>(1000);
        auto inverse   = yaml_servo["inverse"]  .as<bool>(false);
        servos.emplace_back(new revolve::Servo(
                x,
                y,
                z,
                &pigpio,
                pin,
                frequency,
                range,
                inverse
        ));
        std::cout << *servos.back() << std::endl;
    }

    return servos;
}

void control(std::vector<Servo_p> &servos)
{
    revolve::RaspController controller;
}

void reset(std::vector<Servo_p> &servos)
{
    for (const Servo_p &servo: servos)
        servo->off();
}

void center(std::vector<Servo_p> &servos)
{
    for (const Servo_p &servo: servos)
        servo->center();
}