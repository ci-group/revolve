//
// Created by matteo on 14/06/19.
//

#include "RaspController.h"
#include "../brains/controller/DifferentialCPG.h"
#include <yaml-cpp/yaml.h>

using namespace revolve;

RaspController::RaspController(
        std::vector<std::unique_ptr<Actuator> > actuators,
        std::vector<std::unique_ptr<Sensor> > sensors,
        const YAML::Node &conf)
    : revolve_controller(nullptr)
    , actuators(std::move(actuators))
    , sensors(std::move(sensors))
{
    std::string type = conf["type"].as<std::string>("");
    if (type.empty()) {
        throw std::runtime_error("Controller type not set");
    } else if (type == "differential-cpg") {

        DifferentialCPG::ControllerParams params;
        params.reset_neuron_random = false;
        params.use_frame_of_reference = false;
        params.init_neuron_state = 0.707;
        params.range_ub = 1.0;
        params.signal_factor_all = 1.0;
        params.signal_factor_mid = 2.5;
        params.signal_factor_left_right = 2.5;
        params.abs_output_bound = 1.0;

        YAML::Node yaml_weights = conf["weights"];
        for(const YAML::Node &weight: yaml_weights) {
            params.weights.emplace_back(weight.as<double>());
        }

        revolve_controller.reset(
                new DifferentialCPG(params,this->actuators)
        );
    } else {
        throw std::runtime_error("Controller " + type + " not supported (yet)");
    }



}

RaspController::~RaspController() = default;

#include <chrono>
#include <thread>

void RaspController::update()
{
    double step = this->timer.step();
    double time = this->timer.elapsed();
    if (step == 0)
        return;
    this->revolve_controller->update(
        this->actuators,
        this->sensors,
        time,
        step
    );
//    std::this_thread::sleep_for(std::chrono::milliseconds(125));
}
