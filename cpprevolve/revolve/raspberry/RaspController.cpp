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
    this->set_new_controller(conf);
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

void RaspController::set_new_controller(const YAML::Node &conf)
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

        if (conf["reset_neuron_random"].IsDefined()) {
            params.reset_neuron_random = conf["reset_neuron_random"].as<bool>();
            std::cout << "Setting reset_neuron_random to: " << params.reset_neuron_random << std::endl;
        }
        if (conf["use_frame_of_reference"].IsDefined()) {
            params.use_frame_of_reference = conf["use_frame_of_reference"].as<bool>();
            std::cout << "Setting use_frame_of_reference to: " << params.use_frame_of_reference << std::endl;
        }
        if (conf["init_neuron_state"].IsDefined()) {
            params.init_neuron_state = conf["init_neuron_state"].as<double>();
            std::cout << "Setting init_neuron_state to: " << params.init_neuron_state << std::endl;
        }
        if (conf["range_ub"].IsDefined()) {
            params.range_ub = conf["range_ub"].as<double>();
            std::cout << "Setting range_ub to: " << params.range_ub << std::endl;
        }
        if (conf["signal_factor_all"].IsDefined()) {
            params.signal_factor_all = conf["signal_factor_all"].as<double>();
            std::cout << "Setting signal factor all to: " << params.signal_factor_all << std::endl;
        }
        if (conf["signal_factor_mid"].IsDefined()) {
            params.signal_factor_mid = conf["signal_factor_mid"].as<double>();
            std::cout << "Setting signal_factor_mid to: " << params.signal_factor_mid << std::endl;
        }
        if (conf["signal_factor_left_right"].IsDefined()) {
            params.signal_factor_all = conf["signal_factor_left_right"].as<double>();
            std::cout << "Setting signal_factor_left_right to: " << params.signal_factor_left_right << std::endl;
        }
        if (conf["abs_output_bound"].IsDefined()) {
            params.abs_output_bound = conf["abs_output_bound"].as<double>();
            std::cout << "Setting abs_output_bound to: " << params.abs_output_bound << std::endl;
        }

        revolve_controller.reset(
                new DifferentialCPG(params,this->actuators)
        );
    } else {
        throw std::runtime_error("Controller " + type + " not supported (yet)");
    }
}

