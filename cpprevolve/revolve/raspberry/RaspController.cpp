//
// Created by matteo on 14/06/19.
//

#include "RaspController.h"
#include <chrono>
#include <memory>
#include <thread>
#include "../brains/controller/DifferentialCPG.h"
#include "../brains/controller/BrokenDifferentialCPG.h"
#include "AngleToTargetDetector.h"
#include <yaml-cpp/yaml.h>

using namespace revolve::raspberry;

RaspController::RaspController(
        std::vector<std::shared_ptr<Actuator> > actuators,
        std::vector<std::shared_ptr<Sensor> > sensors,
        const YAML::Node &conf)
    : revolve_controller(nullptr)
    , camera(nullptr)
    , actuators(std::move(actuators))
    , sensors(std::move(sensors))
{
    // camera can be nullptr
    this->load_camera(conf["angle_to_target_detector"]);
    this->set_new_controller(conf);
}

RaspController::~RaspController() = default;

void RaspController::update()
{
    const double step = this->timer.step_double();
    const double time = this->timer.elapsed_double();
    if (step == 0)
        return;
    this->revolve_controller->update(
        this->actuators,
        this->sensors,
        time,
        step
    );

    // negative update rate means run as fast as possible
    if (this->update_rate <= std::chrono::milliseconds::zero()) return;

    const Timer::Seconds cpu_time_spent = this->timer.step_elapsed();
    const Timer::Seconds remaining_wait_time = this->update_rate - cpu_time_spent;
    if (remaining_wait_time > Timer::Seconds::zero()) {
        std::this_thread::sleep_for(remaining_wait_time);
    } else {
        std::clog << "CPU too slow, we missed the cycle deadline of " << (remaining_wait_time).count() / -1000  << " ms " << std::endl;
    }
}

void RaspController::load_camera(const YAML::Node &conf)
{
    if (not conf) {
        std::cout << "Camera not found, the camera will be deactivated." << std::endl;
        return;
    }

    int camera_index;
    std::string camera_type = conf["type"].as<std::string>();
    if (camera_type == "raspberry-camera") {
        camera_index = -1;
        std::cout << "Loading Raspberry camera" << std::endl;
    } else if (camera_type == "usb") {
        camera_index = conf["index"].as<int>();
        std::cout << "Loading usb camera at index " << camera_index << std::endl;
    } else {
        throw std::runtime_error("Camera type " + camera_type + "not recognized");
    }

    const unsigned int camera_shrink_factor = conf["shrink_factor"].as<unsigned int>(4);
    const bool show_camera = conf["show_camera"].as<bool>(false);

    std::cout << "Camera shrink_factor( " << camera_shrink_factor << " ) show_camera( " << (show_camera ? "true" : "false") << " )" << std::endl;

    camera.reset(new ::revolve::raspberry::AngleToTargetDetector(camera_index, camera_shrink_factor, show_camera));
}

void RaspController::set_new_controller(const YAML::Node &conf)
{
    // Update rate in ms
    int64_t _update_rate = conf["update_rate"].as<int64_t>(-1);
    this->update_rate = std::chrono::duration_cast<Timer::Seconds>(std::chrono::milliseconds(_update_rate));

    std::string type = conf["type"].as<std::string>("");
    if (type.empty()) {
        throw std::runtime_error("Controller type not set");
    } else if (type == "broken-differential-cpg") {
        BrokenDifferentialCPG::ControllerParams params;
        params.reset_neuron_random = conf["reset_neuron_random"].as<bool>(false);
        params.use_frame_of_reference = conf["use_frame_of_reference"].as<bool>(false);
        params.init_neuron_state = conf["init_neuron_state"].as<double>(0.707);
        params.range_ub = conf["range_ub"].as<double>(1.0);
        params.signal_factor_all = conf["output_signal_factor"].as<double>(1.0);
        params.abs_output_bound = conf["abs_output_bound"].as<double>(1.0);

        YAML::Node yaml_weights = conf["weights"];
        for(const YAML::Node &weight: yaml_weights) {
            params.weights.emplace_back(weight.as<double>());
        }

        revolve_controller = std::make_unique<revolve::BrokenDifferentialCPG>(
                params, this->actuators, camera
        );
    } else if (type == "differential-cpg") {

        DifferentialCPG::ControllerParams params;
        params.reset_neuron_random = conf["reset_neuron_random"].as<bool>(false);
        params.use_frame_of_reference = conf["use_frame_of_reference"].as<bool>(false);
        params.init_neuron_state = conf["init_neuron_state"].as<double>(0.707);
        params.range_ub = conf["range_ub"].as<double>(1.0);
        params.output_signal_factor = conf["output_signal_factor"].as<double>(1.0);
        params.abs_output_bound = conf["abs_output_bound"].as<double>(1.0);

        YAML::Node yaml_weights = conf["weights"];
        for(const YAML::Node &weight: yaml_weights) {
            params.weights.emplace_back(weight.as<double>());
        }

        revolve_controller = std::make_unique<revolve::DifferentialCPG>(
                params, this->actuators, camera
        );
    } else {
        throw std::runtime_error("Controller " + type + " not supported (yet)");
    }
}

