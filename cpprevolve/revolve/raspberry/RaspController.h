//
// Created by matteo on 14/06/19.
//

#ifndef REVOLVE_RASPCONTROLLER_H
#define REVOLVE_RASPCONTROLLER_H

#include <ctime>
#include <yaml-cpp/node/node.h>
#include "../brains/controller/Controller.h"
#include "Timer.h"

namespace revolve {

class RaspController
{
public:
    explicit RaspController(
            std::vector<std::unique_ptr< Actuator > > actuators,
            std::vector<std::unique_ptr< Sensor > > sensors,
            const YAML::Node &conf);

    ~RaspController();

    void update();

    void set_new_controller(const YAML::Node &conf);

private:
    std::unique_ptr<revolve::Controller> revolve_controller;
    Timer timer;
    std::vector< std::unique_ptr< revolve::Actuator > > actuators;
    std::vector< std::unique_ptr< revolve::Sensor > > sensors;
};

}


#endif //REVOLVE_RASPCONTROLLER_H
