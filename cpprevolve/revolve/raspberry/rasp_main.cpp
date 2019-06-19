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
void control(std::vector<Servo_p> &servos, const YAML::Node &controller_conf);
void learner(std::vector<Servo_p> &servos, const YAML::Node &controller_conf);
void move_to(std::vector<Servo_p> &servos, double value);
void test(std::vector<Servo_p> &servos);


int main( int argc, const char* argv[] )
{
    try {
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


        if (argc >= 2) {
            std::string command = std::string(argv[1]);
            if (command == "reset")
                reset(servos);
            else if (command == "center")
                center(servos);
            else if (command == "controller")
                control(servos, config["controller"]);
            else if (command == "learner")
                learner(servos, config["controllers"]);
            else if (command == "test")
                test(servos);
            else if (command == "set" && argc >= 3)
                move_to(servos, atof(argv[2]));
            else
                std::clog << "Command \"" << command << "\" not recognized" << std::endl;
        } else {
            control(servos, config["controller"]);
        }
    } catch (const std::exception &e) {
        std::cerr<<"Exception occurred"<< std::endl;
        std::cerr<<e.what()<< std::endl;
    }

    return 0;
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

void control(std::vector<Servo_p> &servos, const YAML::Node &controller_conf)
{
    std::cout << "Staring controller" << std::endl;
    std::vector<std::unique_ptr<revolve::Sensor>> sensors;
    std::vector<std::unique_ptr<revolve::Actuator>> actuators;
    actuators.reserve(servos.size());
    for (Servo_p &servo: servos) {
        actuators.emplace_back(std::move(servo));
    }

    revolve::RaspController controller(
        std::move(actuators),
        std::move(sensors),
        controller_conf
    );

    while (true) {
        controller.update();
    }
}

void learner(std::vector<Servo_p> &servos, const YAML::Node &controllers_conf)
{
    std::cout << "Staring controller" << std::endl;
    std::vector<std::unique_ptr<revolve::Sensor>> sensors;
    std::vector<std::unique_ptr<revolve::Actuator>> actuators;
    actuators.reserve(servos.size());
    for (Servo_p &servo: servos) {
        actuators.emplace_back(std::move(servo));
    }

    revolve::RaspController controller(
            std::move(actuators),
            std::move(sensors),
            controllers_conf[0]
    );

    Timer timer;
    unsigned short counter = 0;
    for (const YAML::Node &controller_conf: controllers_conf) {
        std::cout << "Loading controller[" << ++counter << "] fitness: " << controller_conf["fitness"].as<double>(-1) << std::endl;
        controller.set_new_controller(controller_conf);
        timer.reset();
        while (timer.elapsed_now() < 30.0) {
            controller.update();
        }
    }

    std::cout << "Evaluation finished, keeping best controller" << std::endl;
    while (true) {
        controller.update();
    }
}

void reset(std::vector<Servo_p> &servos)
{
    std::cout << "Shutting off servos" << std::endl;
    for (const Servo_p &servo: servos)
        servo->off();
}

void center(std::vector<Servo_p> &servos)
{
    std::cout << "Setting servos to center" << std::endl;
    for (const Servo_p &servo: servos)
        servo->center();

    std::cout << "Press enter to continue" << std::endl;
    std::string something;
    std::cin >> something;
}

void move_to(std::vector<Servo_p> &servos, double value)
{
    std::cout << "Setting servos to " << value << std::endl;
    for (const Servo_p &servo: servos)
        servo->move_to_position(value);
    std::cout << "Press enter to continue" << std::endl;
    std::string something;
    std::cin >> something;
}

void test(std::vector<Servo_p> &servos)
{
    std::cout << "Testing servos" << std::endl;

    move_to(servos, -1);
    move_to(servos, -.5);
    move_to(servos, 0);
    move_to(servos, 0.5);
    move_to(servos, 1);
}