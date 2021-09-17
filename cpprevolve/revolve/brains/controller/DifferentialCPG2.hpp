#ifndef REVOLVE_DIFFERENTIAL_CPG_2_HPP
#define REVOLVE_DIFFERENTIAL_CPG_2_HPP

#include "Controller.h"

#include <vector>

#include "actuators/Actuator.h"
#include <boost/numeric/odeint.hpp>

namespace revolve
{

    class DifferentialCPG2 : public Controller
    {
    public:
        struct Parameters
        {
            double initial_neuron_state;
            double output_signal_gain;
            double abs_output_bound;
            std::vector<double> weights;
        };

        DifferentialCPG2(Parameters const &parameters, std::vector<std::shared_ptr<Actuator>> const &actuators);

        void update(
            std::vector<std::shared_ptr<Actuator>> const &actuators,
            std::vector<std::shared_ptr<Sensor>> const &sensors,
            double const time,
            double const dt) override;

    private:
        // indices of neurons corresponding to actuators
        std::vector<size_t> actuator_neurons;

        std::vector<double> neuron_state;

        std::vector<std::vector<double>> ode_matrix;

        // neural network ode solver
        boost::numeric::odeint::runge_kutta4<std::vector<double>> ode_solver;

        void create_neurons(Parameters const &parameters, std::vector<std::shared_ptr<Actuator>> const &actuators);
        void create_ode_matrix(Parameters const &parameters, std::vector<std::shared_ptr<Actuator>> const &actuators);
        void integrate_neural_network(double const time, double const dt);
        void update_actuators(std::vector<std::shared_ptr<Actuator>> const &actuators, double const dt);
    };

}

#endif // REVOLVE_DIFFERENTIAL_CPG_2_HPP
