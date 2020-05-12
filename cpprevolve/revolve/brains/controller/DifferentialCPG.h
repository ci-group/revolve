//
// Created by matteo on 14/06/19.
//

#ifndef REVOLVE_DIFFERENTIALCPG_H
#define REVOLVE_DIFFERENTIALCPG_H

#include "Controller.h"
#include "actuators/Actuator.h"
#include "sensors/Sensor.h"
#include "sensors/AngleToTargetDetector.h"

#include <map>
#include <memory>
#include <boost/numeric/odeint.hpp>
#include <multineat/Genome.h>

typedef std::vector< double > state_type;

namespace revolve
{
class DifferentialCPG
        : public Controller
{
public:
    struct ControllerParams {
        bool reset_neuron_random;
        bool use_frame_of_reference;
        double init_neuron_state;
        double range_ub;
        double output_signal_factor;
        double abs_output_bound;
        std::vector< double > weights;
        /// can be null, indicating that there is no map
        std::unique_ptr<std::map<std::string, std::set<std::string>>> connection_map;
    };

    /// \brief Constructor
    /// \param[in] params Parameters for the controller
    /// \param[in] _actuators Reference to a actuator list
    DifferentialCPG(
            const DifferentialCPG::ControllerParams &params,
            const std::vector<std::shared_ptr<Actuator>> &_actuators,
            std::shared_ptr<AngleToTargetDetector> angle_to_target_sensor = nullptr);

    /// \brief Constructor for Controller with config CPPN
    /// \param[in] params Parameters for the controller
    /// \param[in] _actuators Reference to a actuator list
    /// \param[in] config_cppn_genome Reference to the genome for configuring the weights in CPG
    DifferentialCPG(
            const DifferentialCPG::ControllerParams &params,
            const std::vector<std::shared_ptr<Actuator>> &_actuators,
            const NEAT::Genome &config_cppn_genome,
            std::shared_ptr<AngleToTargetDetector> angle_to_target_sensor = nullptr);

    /// \brief Destructor
    virtual ~DifferentialCPG();

    /// \brief The default update method for the controller
    /// \param[in] _actuators Actuator list
    /// \param[in] _sensors Sensor list
    /// \param[in] _time Current world time
    /// \param[in] _step Current time step
    virtual void update(
            const std::vector<std::shared_ptr<Actuator>> &actuators,
            const std::vector<std::shared_ptr<Sensor>> &sensors,
            double _time,
            double _step) override;

    /// \brief Set the connection weights of the Controller and make sure the matrix is set appropriately
    /// \param[in] The weights to be set
    void set_connection_weights(std::vector<double> weights);

    /// \brief Return the weights of the connections
    std::vector<double> get_connection_weights();

protected:

    void step(double time, double step);

    void init_params_and_connections(const ControllerParams &params, const std::vector<std::shared_ptr<Actuator>> &actuators);

    void set_ode_matrix();

private:
    /// \brief Function that resets neuron state
    void reset_neuron_state();

    /// \brief function that transforms the value of the CPG A-neurons and returns the correct output for the actuators
    double output_function(double input) const;

public:
    std::map< std::tuple< int, int, int >, size_t > motor_coordinates;

protected:
    /// \brief Register of motor IDs and their x,y-coordinates
//    std::map< std::string, std::tuple< int, int > > positions;

    struct Neuron {
        int x, y, z, w;
        double bias, gain, state;
        int frame;
    };

    /// \brief Register of individual neurons in x,y,z,w-coordinates
    /// \details x,y,z-coordinates define position of a robot's module and
    // w-coordinate define A or B neuron (w=1 or -1 respectively). Stored
    // values are a bias, gain, state and frame of reference of each neuron.
    std::vector< Neuron > neurons;

    /// \brief Register of connections between neighnouring neurons
    /// \details Coordinate set of two neurons (x1, y1, z1, w1) and (x2, y2, z2, w2)
    ///   define a connection. The value is the weight index corresponding to this connection.
    std::map< std::tuple< int, int, int, int, int, int, int, int>, int >
    connections;

    /// \brief Runge-Kutta 45 stepper
    boost::numeric::odeint::runge_kutta4< state_type > stepper;

    /// \brief Used for ODE-int
    std::vector<std::vector<double>> ode_matrix;

    /// \brief Angle sensor holder
    std::shared_ptr<::revolve::AngleToTargetDetector> angle_to_target_sensor;

private:
    /// \brief Used to determine the next state array
    double *next_state;

    /// \brief Used to determine the output to the motors array
    double *output;

    /// \brief Limbo optimizes in [0,1]
    double range_lb;

    /// \brief Limbo optimizes in [0,1]
    double range_ub;

    /// \brief Loaded weights
    std::vector<double> connection_weights;

    /// \brief The number of weights to optimize
    size_t n_weights;

    /// \brief Factor to multiply output signal with
    double output_signal_factor;

    /// \brief When reset a neuron state,do it randomly:
    bool reset_neuron_random;

    /// \brief Holds the number of motors in the robot
    size_t n_motors;

    /// \brief Initial neuron state
    double init_neuron_state;

    /// \brief Use frame of reference {-1,0,1} version or not
    bool use_frame_of_reference;

    double abs_output_bound;

};

}

#endif //REVOLVE_DIFFERENTIALCPG_H
