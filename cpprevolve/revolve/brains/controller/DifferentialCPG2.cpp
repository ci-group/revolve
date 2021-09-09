#include "DifferentialCPG2.hpp"

#include <algorithm>
#include <functional>

using namespace revolve;

DifferentialCPG2::DifferentialCPG2(DifferentialCPG2::Parameters const &parameters, std::vector<std::shared_ptr<Actuator>> const &actuators)
{
    create_neurons(parameters, actuators);
    create_ode_matrix(parameters, actuators);
}

void DifferentialCPG2::create_neurons(Parameters const &parameters, std::vector<std::shared_ptr<Actuator>> const &actuators)
{
    // create two neurons per actuator
    // save index of first neuron as output neuron for an actuator
    for (size_t i = 0; i < actuators.size(); ++i)
    {
        actuator_neurons.push_back(neuron_state.size());
        neuron_state.push_back(parameters.initial_neuron_state);
        neuron_state.push_back(parameters.initial_neuron_state);
    }
}

void DifferentialCPG2::create_ode_matrix(Parameters const &parameters, std::vector<std::shared_ptr<Actuator>> const &actuators)
{
    // reserve space for matrix
    ode_matrix.reserve(actuators.size());
    for (size_t i = 0; i < actuators.size(); ++i)
    {
        ode_matrix.emplace_back(std::vector<double>(actuators.size(), 0));
    }

    size_t external_weight_index = actuators.size();

    for (size_t i = 0; i < actuators.size(); ++i)
    {
        // internal weights
        ode_matrix[i * 2][i * 2 + 1] = parameters.weights[i];
        ode_matrix[i * 2 + 1][i * 2] = -parameters.weights[i];

        // external weights
        double const x1 = actuators[i]->coordinate_x();
        double const y1 = actuators[i]->coordinate_y();
        double const z1 = actuators[i]->coordinate_z();

        for (size_t j = i + 1; j < actuators.size(); ++i)
        {
            double const x2 = actuators[j]->coordinate_x();
            double const y2 = actuators[j]->coordinate_y();
            double const z2 = actuators[j]->coordinate_z();

            double const dist_x = std::fabs(x1 - x2);
            double const dist_y = std::fabs(y1 - y2);
            double const dist_z = std::fabs(z1 - z2);

            // connect moore neighbours
            if (dist_x < 1.01 && dist_y < 1.01 && dist_z < 1.01)
            {
                if (parameters.weights.size() - 1 < external_weight_index)
                {
                    std::cerr << "Not enough weights provided for DifferentialCPG2 controller. Expected at least " << external_weight_index + 1 << ". Throwing error..\n";
                    throw std::runtime_error(std::string("Not enough weights provided for DifferentialCPG2 controller. Expected at least ") + std::to_string(external_weight_index + 1) + ".");
                }
                ode_matrix[i * 2][j * 2] = parameters.weights[external_weight_index];
                ode_matrix[j * 2][i * 2] = -parameters.weights[external_weight_index];
                external_weight_index += 1;
            }
        }
    }

    if (parameters.weights.size() != external_weight_index)
    {
        std::cerr << "Too many weights provided for DifferentialCPG2 controller. Expected exactly " << external_weight_index << ". Throwing error..\n";
        throw std::runtime_error(std::string("Too many weights provided for DifferentialCPG2 controller. Expected exactly ") + std::to_string(external_weight_index) + ".");
    }
}

void DifferentialCPG2::update(
    std::vector<std::shared_ptr<Actuator>> const &actuators,
    std::vector<std::shared_ptr<Sensor>> const &sensors,
    double const time,
    double const dt)
{
    integrate_neural_network(time, dt);
    update_actuators(actuators, dt);
}

void DifferentialCPG2::integrate_neural_network(double const time, double const dt)
{
    ode_solver.do_step(
        [this](std::vector<double> const &state, std::vector<double> &dxdt, double)
        {
            for (size_t i = 0; i < state.size(); ++i)
            {
                dxdt[i] = state[i] * std::accumulate(ode_matrix[i].begin(), ode_matrix[i].end(), 0, std::plus<double>());
            }
        },
        neuron_state,
        time,
        dt);
}

void DifferentialCPG2::update_actuators(std::vector<std::shared_ptr<Actuator>> const &actuators, double const dt)
{
    for (size_t i = 0; i < actuators.size(); ++i)
    {
        actuators[i]->write(&neuron_state[actuator_neurons[i]], dt);
    }
}
