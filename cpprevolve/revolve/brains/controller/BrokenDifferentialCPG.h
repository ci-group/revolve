//
// Created by matteo on 14/06/19.
//

#pragma once

#include "Controller.h"
#include "actuators/Actuator.h"
#include "sensors/Sensor.h"
#include "sensors/AngleToTargetDetector.h"
#include <map>
#include <boost/numeric/odeint.hpp>
#include <Eigen/Geometry>

typedef std::vector< double > state_type;

namespace revolve
{
class BrokenDifferentialCPG
        : public Controller
{
public:
    struct ControllerParams {
        bool reset_neuron_random;
        bool use_frame_of_reference;
        double init_neuron_state;
        double range_ub;
        double signal_factor_all;
        double signal_factor_mid;
        double signal_factor_left_right;
        double abs_output_bound;
        std::vector< double > weights;
    };

    /// \brief Constructor
    /// \param[in] _modelName Name of the robot
    /// \param[in] _node The brain node
    /// \param[in] _motors Reference to a motor list, it be reordered
    /// \param[in] _sensors Reference to a sensor list, it might be reordered
    BrokenDifferentialCPG(
            const ControllerParams &params,
            const std::vector< std::shared_ptr < Actuator > > &_actuators,
            std::shared_ptr<AngleToTargetDetector> angle_to_target_sensor = nullptr);

    /// \brief Destructor
    virtual ~BrokenDifferentialCPG();

    /// \brief The default update method for the controller
    /// \param[in] _motors Motor list
    /// \param[in] _sensors Sensor list
    /// \param[in] _time Current world time
    /// \param[in] _step Current time step
    virtual void update(
            const std::vector< std::shared_ptr < Actuator > > &actuators,
            const std::vector< std::shared_ptr < Sensor > > &sensors,
            const double _time,
            const double _step) override;

protected:

    void step(
            const double time,
            const double step);

    void set_ode_matrix();

private:
    /// \brief Function that resets neuron state
    void reset_neuron_state();

    /// \brief function that transforms the value of the CPG A-neurons and returns the correct output for the actuators
    double output_function(double input) const;

public:
    std::map< std::tuple< double, double >, size_t > motor_coordinates;

protected:
    /// \brief Register of motor IDs and their x,y-coordinates
//    std::map< std::string, std::tuple< int, int > > positions;

    /// \brief Register of individual neurons in x,y,z-coordinates
    /// \details x,y-coordinates define position of a robot's module and
    // z-coordinate define A or B neuron (z=1 or -1 respectively). Stored
    // values are a bias, gain, state and frame of reference of each neuron.
    std::map< std::tuple< int, int, int >, std::tuple< double, double, double, int > >
            neurons;

    /// \brief Register of connections between neighnouring neurons
    /// \details Coordinate set of two neurons (x1, y1, z1) and (x2, y2, z2)
    // define a connection. The second tuple contains 1: the connection value and
    // 2: the weight index corresponding to this connection.
    std::map< std::tuple< int, int, int, int, int, int >, std::tuple<int, int > >
            connections;

    /// \brief Runge-Kutta 45 stepper
    boost::numeric::odeint::runge_kutta4< state_type > stepper;

    /// \brief Used for ODE-int
    std::vector<std::vector<double>> ode_matrix;

private:
    /// \brief Used to determine the next state array
    double *next_state;

    /// \brief Used to determine the output to the motors array
    double *output;

    /// \brief Limbo optimizes in [0,1]
    double range_lb;

    /// \brief Limbo optimizes in [0,1]
    double range_ub;

    /// \brief Loaded sample
    Eigen::VectorXd sample;

    /// \brief The number of weights to optimize
    size_t n_weights;

    /// \brief Factor to multiply output signal with
    double signal_factor_all_;

    /// \brief Factor to multiply output signal with
    double signal_factor_mid;

    /// \brief Factor to multiply output signal with
    double signal_factor_left_right;

    /// \brief When reset a neuron state,do it randomly:
    bool reset_neuron_random;

    /// \brief Holds the number of motors in the robot
    size_t n_motors;

    /// \brief Initial neuron state
    double init_neuron_state;

    /// \brief Use frame of reference {-1,0,1} version or not
    bool use_frame_of_reference;

    double abs_output_bound;

// targeted locomotion stuff
    std::shared_ptr<AngleToTargetDetector> angle_to_target_sensor;
};

}
