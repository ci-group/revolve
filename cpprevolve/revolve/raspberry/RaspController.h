//
// Created by matteo on 14/06/19.
//

#ifndef REVOLVE_RASPBERRY_RASPCONTROLLER_H
#define REVOLVE_RASPBERRY_RASPCONTROLLER_H

#include <ctime>
#include <yaml-cpp/node/node.h>
#include "../brains/controller/Controller.h"
#include "../brains/controller/sensors/AngleToTargetDetector.h"
#include "Timer.h"

namespace revolve {
namespace raspberry {

class RaspController {
public:
    explicit RaspController(
            std::vector<std::shared_ptr<::revolve::Actuator> > actuators,
            std::vector<std::shared_ptr<::revolve::Sensor> > sensors,
            const YAML::Node &conf);

    ~RaspController();

    void update();

    void load_camera(const YAML::Node &conf);
    void set_new_controller(const YAML::Node &conf);

private:
    std::unique_ptr<::revolve::Controller> revolve_controller;
    std::shared_ptr<::revolve::AngleToTargetDetector> camera;
    Timer timer;
    std::vector<std::shared_ptr<::revolve::Actuator> > actuators;
    std::vector<std::shared_ptr<::revolve::Sensor> > sensors;

    /// Update rate in seconds
    Timer::Seconds update_rate;
};

}
}
#endif //REVOLVE_RASPBERRY_RASPCONTROLLER_H
