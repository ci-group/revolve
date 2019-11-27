/*
 * Copyright (C) 2015-2018 Vrije Universiteit Amsterdam
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * Description: TODO: <Add brief description about file purpose>
 * Author: Milan Jelisavcic & Maarten van Hooft
 * Date: December 29, 2018
 *
 */

#include "DifferentialCPG.h"

// STL macros
#include <algorithm>
#include <cstdlib>
#include <ctime>
#include <iostream>
#include <iomanip>
#include <map>
#include <memory>
#include <random>
#include <tuple>
#include <boost/algorithm/string/split.hpp>
#include <boost/algorithm/string/classification.hpp>
#include <multineat/Genome.h>

// Project headers
#include "actuators/Actuator.h"
#include "sensors/Sensor.h"

// define this if you want to debug the weights of the CPG network
//#define DifferentialCPG_PRINT_INFO

// Define namespaces
using namespace revolve;

/**
 * Constructor for DifferentialCPG class without cppn config.
 *
 * @param _model
 * @param robot_config
 */
DifferentialCPG::DifferentialCPG(
        const DifferentialCPG::ControllerParams params,
        const std::vector<std::shared_ptr<Actuator>> &actuators)
        : next_state(nullptr)
        , n_motors(actuators.size())
        , output(new double[actuators.size()])
        , sample(actuators.size(), 0)
{
    this->init_params_and_connections(params, actuators);
    // Save weights for brain
    assert(params.weights.size() == n_weights);
    sample.resize(n_weights, 0);
    for(size_t j = 0; j < n_weights; j++)
    {
        sample.at(j) = params.weights.at(j);
    }

    // Set ODE matrix at initialization
    set_ode_matrix();

    std::cout << "Brain has been loaded." << std::endl;
}

/**
 * Constructor for DifferentialCPG class that loads weights from CPPN.
 *
 * @param params
 * @param actuators
 * @param config_cppn_genome
 */
DifferentialCPG::DifferentialCPG(
        DifferentialCPG::ControllerParams params,
        const std::vector<std::shared_ptr<Actuator>> &actuators,
        const NEAT::Genome &gen)
        : next_state(nullptr)
        , n_motors(actuators.size())
        , output(new double[actuators.size()])
        , sample(actuators.size(), 0)
{
    this->init_params_and_connections(params, actuators);

    // build the NN according to the genome
    NEAT::NeuralNetwork net;
    gen.BuildPhenotype(net);

    // get weights for each connection
    // assuming that connections are distinct for each direction
    sample.resize(n_weights, 0);
    std::vector<double> inputs(8);

    for(const std::pair< const std::tuple< int, int, int>, size_t > &motor: motor_coordinates)
    {
        size_t k = motor.second;

        // convert tuple to vector
        std::tie(inputs[0], inputs[1], inputs[2]) = motor.first;
        inputs[3] = 1;
        std::tie(inputs[4], inputs[5], inputs[6]) = motor.first;
        inputs[7] = -1;

        net.Input(inputs);
        net.Activate();
        double weight = net.Output()[0];
#ifdef DifferentialCPG_PRINT_INFO
        std::cout << "Creating weight ["
                  << inputs[0] << ';' << inputs[1] << ';' << inputs[2] << ';' << inputs[3] << '-'
                  << inputs[4] << ';' << inputs[5] << ';' << inputs[6] << ';' << inputs[7]
                  << "] to sample[" << k << "]\t-> " << weight << std::endl;
#endif
        sample.at(k) = weight;  // order of weights corresponds to order of connections.
    }

    for(const std::pair<const std::tuple<int, int, int, int, int, int, int, int>, int > &con : connections)
    {
        int k = con.second;
        // convert tuple to vector
        std::tie(inputs[0], inputs[1], inputs[2], inputs[3], inputs[4], inputs[5], inputs[6], inputs[7]) = con.first;
        net.Input(inputs);
        net.Activate();
        double weight = net.Output()[0];
#ifdef DifferentialCPG_PRINT_INFO
        std::cout << "Creating weight ["
                  << inputs[0] << ';' << inputs[1] << ';' << inputs[2] << ';' << inputs[3] << '-'
                  << inputs[4] << ';' << inputs[5] << ';' << inputs[6] << ';' << inputs[7]
                  << "] to sample[" << k << "]\t-> " << weight << std::endl;
#endif
        sample.at(k) = weight;  // order of weights corresponds to order of connections.
    }

    // Set ODE matrix at initialization
    set_ode_matrix();

    std::cout << "DifferentialCPG brain with CPPN configuration has been loaded." << std::endl;
}

void DifferentialCPG::init_params_and_connections(const ControllerParams &params, const std::vector<std::shared_ptr<Actuator>> &actuators)
{
    // Controller parameters
    this->reset_neuron_random = params.reset_neuron_random;
    this->init_neuron_state = params.init_neuron_state;
    this->range_lb = -params.range_ub;
    this->range_ub = params.range_ub;
    this->use_frame_of_reference = params.use_frame_of_reference;
    this->signal_factor_all_ = params.signal_factor_all;
    this->signal_factor_mid = params.signal_factor_mid;
    this->signal_factor_left_right = params.signal_factor_left_right;
    this->abs_output_bound = params.abs_output_bound;
    this->loadedWeights = params.weights;

    size_t j=0;
    for (const std::shared_ptr<Actuator> &actuator: actuators)
    {
        // Pass coordinates
        int coord_x = actuator->coordinate_x();
        int coord_y = actuator->coordinate_y();
        int coord_z = actuator->coordinate_z();
        this->motor_coordinates[{coord_x, coord_y, coord_z}] = j;

        // Set frame of reference
        int frame_of_reference = 0;
        // We are a left neuron
        if (coord_x < 0)
        {
            frame_of_reference = -1;
        }
            // We are a right neuron
        else if (coord_x > 0)
        {
            frame_of_reference = 1;
        }

        // Save neurons: bias/gain/state. Make sure initial states are of different sign.
        neurons.emplace_back( Neuron {coord_x, coord_y, coord_z,  1, 0.f, 0.f,  this->init_neuron_state, frame_of_reference} );
        neurons.emplace_back( Neuron {coord_x, coord_y, coord_z, -1, 0.f, 0.f, -this->init_neuron_state, frame_of_reference} );

        // These connections don't have to be made explicit
        //this->connections[{coord_x, coord_y, coord_z, 1, coord_x, coord_y, coord_z, -1}] = j;
        //this->connections[{coord_x, coord_y, coord_z, -1, coord_x, coord_y, coord_z, 1}] = j;
        j++;
    }

    // Add connections between neighbouring neurons
    size_t i = j;
    for (const std::shared_ptr<Actuator> &actuator: actuators)
    {
        // Get name and x,y-coordinates of all neurons.
        const double x = actuator->coordinate_x();
        const double y = actuator->coordinate_y();
        const double z = actuator->coordinate_z();

        // Continue to next iteration in case there is already a connection between the 1 and -1 neuron.
        // These checks feel a bit redundant.
        // if A->B connection exists.
        if (this->connections.count({x, y, z, 1, x, y, z, -1}) > 0)
        {
            continue;
        }
        // if B->A connection exists:
        if (this->connections.count({x, y, z, -1, x, y, z, 1}) > 0)
        {
            continue;
        }

        // Loop over all positions. We call it neighbours, but we still need to check if they are a neighbour.
        for (const std::shared_ptr<Actuator> &neighbour: actuators)
        {
            // Get information of this neuron (that we call neighbour).
            const double near_x = neighbour->coordinate_x();
            const double near_y = neighbour->coordinate_y();
            const double near_z = neighbour->coordinate_z();

            // If there is a node that is a Moore neighbour, we set it to be a neighbour for their A-nodes.
            // Thus the connections list only contains connections to the A-neighbourhood, and not the
            // A->B and B->A for some node (which makes sense).
            const double dist_x = std::fabs(x - near_x);
            const double dist_y = std::fabs(y - near_y);

            // TODO: Verify for non-spiders
            if (std::fabs(dist_x + dist_y - 2) < 0.01)
            {
                if(this->connections.count({x, y, z, 1, near_x, near_y, near_z, 1}) == 0 and
                   this->connections.count({near_x, near_y, near_z, 1, x, y, z, 1}) == 0)
                {
#ifdef DifferentialCPG_PRINT_INFO
                    std::cout << "Creating connnection ["
                              << x << ';' << y << ';' << z << ';' << 1 << '-'
                              << near_x << ';' << near_y << ';' << near_z << ';' << 1
                              << "] to sample[" << i << ']' << std::endl;
#endif
                    this->connections[{x, y, z, 1, near_x, near_y, near_z, 1}] = i;
                    //this->connections[{near_x, near_y, near_z, 1, x, y, z, 1}] = i;
                    i++;
                }
            }
        }
    }

    // Initialise array of neuron states for Update() method
    this->next_state = new double[this->neurons.size()];

    // the size is: external connection weights + internal CPG weights
    this->n_weights = (int)(this->connections.size()) + this->n_motors;
}

/**
 * Destructor
 */
DifferentialCPG::~DifferentialCPG()
{
    delete[] this->next_state;
    delete[] this->output;
}

/**
 * Callback function that defines the movement of the robot
 *
 * @param _motors
 * @param _sensors
 * @param _time
 * @param _step
 */
void DifferentialCPG::update(
        const std::vector<std::shared_ptr<Actuator>> &actuators,
        const std::vector<std::shared_ptr<Sensor>> &sensors,
        const double time,
        const double step)
{
    // Send new signals to the motors
    this->step(time, step);

    unsigned int p = 0;
    for (const auto &actuator: actuators)
    {
        actuator->write(this->output + p, step);
        p += actuator->n_outputs();
    }
}

/**
 * Make matrix of weights A as defined in dx/dt = Ax.
 * Element (i,j) specifies weight from neuron i to neuron j in the system of ODEs
 */
void DifferentialCPG::set_ode_matrix()
{
    // Initiate new matrix
    std::vector<std::vector<double>> matrix;
    matrix.reserve(this->neurons.size());

    // Fill with zeroes
    for(size_t i =0; i <this->neurons.size(); i++)
    {
        // Initialize row in matrix with zeros
        const std::vector< double > row (this->neurons.size(), 0);
        matrix.emplace_back(row);
    }

    // Process A<->A connections
    int index = 0;
    for (const Neuron &neuron: neurons)
    {
        int x = neuron.x;
        int y = neuron.y;
        int z = neuron.z;
        if (neuron.w < 0) {
            continue;
        }
        size_t k = motor_coordinates.at({x, y, z});
#ifdef DifferentialCPG_PRINT_INFO
        std::cout << "Setting connection ["
                  << x << ';' << y << ';' << z << ';' << 1 << '-'
                  << x << ';' << y << ';' << z << ';' << -1
                  << "] to sample[" << k << "]\t-> " << this->sample.at(k) << std::endl;
#endif
        auto weight = this->sample.at(k) *
                 (this->range_ub - this->range_lb) + this->range_lb;
        size_t i = index;
        size_t c = index + 1;
        matrix.at(i).at(c) = weight;
        matrix.at(c).at(i) = -weight;
        index+=2;
    }

    // A<->B connections
    index++;
    int k = 0;
    std::vector<std::string> connections_seen;

    for (auto const &connection : this->connections)
    {
        // Get connection information
        int x1, y1, z1, w1, x2, y2, z2, w2;
        std::tie(x1, y1, z1, w1, x2, y2, z2, w2) = connection.first;

        // Find location of the two neurons in this->neurons list
        int l1 = -1;
        int l2 = -1;
        int c = 0;
        for(const Neuron &neuron : this->neurons)
        {
            int x = neuron.x;
            int y = neuron.y;
            int z = neuron.z;
            int w = neuron.w;
            if (x == x1 and y == y1 and z == z1 and w == w1)
            {
                l1 = c;
            }
            else if (x == x2 and y == y2 and z == z2 and w == w2)
            {
                l2 = c;
            }
            // Update counter
            c++;
        }

        // Add connection to seen connections
        if(l1 > l2)
        {
            // swap l1 and l2
            int l1_old = l1;
            l1 = l2;
            l2 = l1_old;
        }
        std::string connection_string = std::to_string(l1) + "-" + std::to_string(l2);

        // if not in list, add to list
        auto connections_list = std::find(connections_seen.begin(), connections_seen.end(), connection_string);
        if(connections_list == connections_seen.end())
        {
            connections_seen.push_back(connection_string);
        }
        else // else continue to next iteration
        {
            // actually, we should never encounter this, every connection should appear only once
            std::cerr << "Should not see the same connection appearing twice" << std::endl;
            throw std::runtime_error("Should not see the same connection appearing twice");
            continue;
        }

        const int sample_index = connections[{x1, y1, z1, w1, x2, y2, z2, w2}];
#ifdef DifferentialCPG_PRINT_INFO
        std::cout << "Setting connection ["
                  << x1 << ';' << y1 << ';' << z1 << ';' << w1 << '-'
                  << x2 << ';' << y2 << ';' << z2 << ';' << w2
                  << "] to sample[" << sample_index << "]\t-> " << this->sample.at(sample_index) << std::endl;
#endif

        // Get weight
        const auto w  = this->sample.at(sample_index) *
                        (this->range_ub - this->range_lb) + this->range_lb;

        // Set connection in weight matrix
        matrix[l1][l2] = w;
        matrix[l2][l1] = -w;
        k++;
    }

#ifdef DifferentialCPG_PRINT_INFO
    std::cout << "DifferentialCPG: added " << connections_seen.size() << " connections" << std::endl;
#endif

    // Update matrix
    this->ode_matrix = std::move(matrix);

    // Reset neuron state
    this->reset_neuron_state();

#ifdef DifferentialCPG_PRINT_INFO
    std::cout << " Matrix " << std::endl;
    for (const auto &row: ode_matrix)
    {

        std::cout << "| ";
        for (double value: row)
        {
            std::cout << std::setw(5) << std::setprecision(2) << value << ' ';
        }
        std::cout << '|' << std::endl;
    }
#endif

}


/**
 *  Set states back to original value (that is on the unit circle)
 */
void DifferentialCPG::reset_neuron_state()
{
    for(Neuron &neuron : this->neurons)
    {
        neuron.bias = 0.0f;
        neuron.gain = 0.0f;
        if (this->reset_neuron_random)
        {
            neuron.state = ((double) rand() / (RAND_MAX)) * 2 * this->init_neuron_state - this->init_neuron_state;
        }
        else if (neuron.w == -1)
        {
            // Neuron B
            neuron.state = -this->init_neuron_state;
        }
        else
        {
            // Neuron A
            neuron.state = this->init_neuron_state;
        }
    }
}

/**
 * Step function that is called from within Update()
 *
 * @param _time
 * @param _output
 */
void DifferentialCPG::step(
        const double time,
        const double dt)
{
    int neuron_count = 0;
    for (const Neuron &neuron : this->neurons)
    {
        double recipient_state = neuron.state;

        // Save for ODE
        this->next_state[neuron_count] = recipient_state;
        neuron_count++;
    }

    // Copy values from next_state into x for ODEINT
    state_type x(this->neurons.size());
    for (size_t i = 0; i < this->neurons.size(); i++)
    {
        x[i] = this->next_state[i];
    }

    // Perform one step
    stepper.do_step(
            [this](const state_type &x, state_type &dxdt, double t)
            {
                for(size_t i = 0; i < this->neurons.size(); i++)
                {
                    dxdt[i] = 0;
                    for(size_t j = 0; j < this->neurons.size(); j++)
                    {
                        dxdt[i] += x[j]*this->ode_matrix[j][i];
                    }
                }
            },
            x,
            time,
            dt);

    // Copy values into nextstate
    for (size_t i = 0; i < this->neurons.size(); i++)
    {
        this->next_state[i] = x[i];
    }

    // Loop over all neurons to actually update their states. Note that this is a new outer for loop
    auto i = 0; auto j = 0;
    for (Neuron &neuron : this->neurons)
    {
        // Get bias gain and state for this neuron. Note that we don't take the coordinates.
        // However, they are implicit as their order did not change.
        int x = neuron.x;
        int y = neuron.y;
        int z = neuron.z;
        int frame_of_reference = neuron.frame;
        neuron.state = this->next_state[i];
        j = this->motor_coordinates[{x,y,z}];
        // Should be one, as output should be based on +1 neurons, which are the A neurons
        if (i % 2 == 1)
        {
            // TODO: Add Milan's function here as soon as things are working a bit
            // f(a) = (w_ao*a - bias)*gain

            // Apply saturation formula
            auto x_input = this->next_state[i];

            // Use frame of reference
            if(use_frame_of_reference)
            {

                if (std::abs(frame_of_reference) == 1)
                {
                    this->output[j] = this->signal_factor_left_right*this->abs_output_bound*((2.0)/(1.0 + std::pow(2.718, -2.0 * x_input / this->abs_output_bound)) - 1);
                }
                else if (frame_of_reference == 0)
                {
                    this->output[j] = this->signal_factor_mid*this->abs_output_bound*((2.0)/(1.0 + std::pow(2.718, -2.0 * x_input / this->abs_output_bound)) - 1);
                }
                else
                {
                    std::clog << "WARNING: frame_of_reference not in {-1,0,1}." << std::endl;
                }

            }
            // Don't use frame of reference
            else
            {
                this->output[j] = this->signal_factor_all_*this->abs_output_bound*((2.0)/(1.0 + std::pow(2.718, -2.0 * x_input / this->abs_output_bound)) - 1);
            }
        }
        i++;
    }
}
