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

#include "BrokenDifferentialCPG.h"

// STL macros
#include <cstdlib>
#include <map>
#include <algorithm>
#include <random>
#include <tuple>
#include <time.h>
#include <boost/algorithm/string/split.hpp>
#include <boost/algorithm/string/classification.hpp>
#include <Eigen/Geometry>

// Project headers
#include "actuators/Actuator.h"

#include "sensors/Sensor.h"

// TODO: Resolve odd behaviour at the end of the validation procedure
// This behaviour is not present if you directly load a trained controller

// Define namespaces
using namespace revolve;

/**
 * Constructor for BrokenDifferentialCPG class.
 *
 * @param _model
 * @param robot_config
 */
BrokenDifferentialCPG::BrokenDifferentialCPG(
        const BrokenDifferentialCPG::ControllerParams &params,
        const std::vector< std::shared_ptr< Actuator > > &actuators,
        std::shared_ptr<AngleToTargetDetector> angle_to_target_sensor)
          : Controller(ControllerType::DIFFERENTIAL_CPG)
          , next_state(nullptr)
          , n_motors(actuators.size())
          , output(new double[actuators.size()])
          , angle_to_target_sensor(std::move(angle_to_target_sensor))
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

    if (use_frame_of_reference and not this->angle_to_target_sensor) {
        std::clog << "WARNING!: use_frame_of_reference is activated but no angle_to_target_sensor camera is configured. "
                     "Disabling the use of the frame of reference" << std::endl;
        use_frame_of_reference = false;
    }

    size_t j=0;
    for (const std::shared_ptr<Actuator> &actuator: actuators)
    {
        // Pass coordinates
        auto coord_x = actuator->coordinate_x();
        auto coord_y = actuator->coordinate_y();
        this->motor_coordinates[{coord_x, coord_y}] = j;

        // Set frame of reference
        int frame_of_reference = 0;
        // We are a left neuron
        if (coord_y < 0)
        {
            frame_of_reference = -1;
        }
            // We are a right neuron
        else if (coord_y > 0)
        {
            frame_of_reference = 1;
        }

        // Save neurons: bias/gain/state. Make sure initial states are of different sign.
        this->neurons[{coord_x, coord_y, 1}] = {0.f, 0.f, this->init_neuron_state, frame_of_reference}; //Neuron A
        this->neurons[{coord_x, coord_y, -1}] = {0.f, 0.f, -this->init_neuron_state, frame_of_reference}; // Neuron B
        j++;
    }

    // Add connections between neighbouring neurons
    int i = 0;
    for (const std::shared_ptr<Actuator> &actuator: actuators)
    {
        // Get name and x,y-coordinates of all neurons.
        double x = actuator->coordinate_x();
        double y = actuator->coordinate_y();

        // Continue to next iteration in case there is already a connection between the 1 and -1 neuron.
        // These checks feel a bit redundant.
        // if A->B connection exists.
        if (this->connections.count({x, y, 1, x, y, -1}) > 0)
        {
            continue;
        }
        // if B->A connection exists:
        if (this->connections.count({x, y, -1, x, y, 1}) > 0)
        {
            continue;
        }

        // Loop over all positions. We call it neighbours, but we still need to check if they are a neighbour.
        for (const std::shared_ptr<Actuator> &neighbour: actuators)
        {
            // Get information of this neuron (that we call neighbour).
            double near_x = neighbour->coordinate_x();
            double near_y = neighbour->coordinate_y();

            // If there is a node that is a Moore neighbour, we set it to be a neighbour for their A-nodes.
            // Thus the connections list only contains connections to the A-neighbourhood, and not the
            // A->B and B->A for some node (which makes sense).
            double dist_x = std::fabs(x - near_x);
            double dist_y = std::fabs(y - near_y);

            // TODO: Verify for non-spiders
            if (std::fabs(dist_x + dist_y - 2) < 0.01)
            {
                if(std::get<0>(this->connections[{x, y, 1, near_x, near_y, 1}]) != 1 or
                   std::get<0>(this->connections[{near_x, near_y, 1, x, y, 1}]) != 1)
                {
                    this->connections[{x, y, 1, near_x, near_y, 1}] = std::make_tuple(1, i);
                    this->connections[{near_x, near_y, 1, x, y, 1}] = std::make_tuple(1, i);
                    i++;
                }
            }
        }
    }

    // Initialise array of neuron states for Update() method
    this->next_state = new double[this->neurons.size()];
    this->n_weights = (int)(this->connections.size()/2) + this->n_motors;

    // Loading Brain

    // Save weights for brain
    assert(params.weights.size() == this->n_weights);
    this->sample.resize(this->n_weights);
    for(size_t j = 0; j < this->n_weights; j++)
    {
        this->sample(j) = params.weights.at(j);
    }

    // Set ODE matrix at initialization
    this->set_ode_matrix();

    std::cout << "Brain has been loaded." << std::endl;
}

/**
 * Destructor
 */
BrokenDifferentialCPG::~BrokenDifferentialCPG()
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
void BrokenDifferentialCPG::update(
        const std::vector< std::shared_ptr < Actuator > > &actuators,
        const std::vector< std::shared_ptr < Sensor > > &sensors,
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
void BrokenDifferentialCPG::set_ode_matrix(){
    // Initiate new matrix
    std::vector<std::vector<double>> matrix;

    // Fill with zeroes
    for(size_t i =0; i <this->neurons.size(); i++)
    {
        // Initialize row in matrix with zeros
        std::vector< double > row;
        for (size_t j = 0; j < this->neurons.size(); j++)
        {
            row.push_back(0);
        }
        matrix.push_back(row);
    }

    // Process A<->B connections
    int index = 0;
    for(size_t i =0; i <this->neurons.size(); i++)
    {
        // Get correct index
        int c = 0;
        if (i%2 == 0){
            c = i + 1;
        }
        else{
            c = i - 1;
        }

        // Add a/b connection weight
        index = (int)(i/2);
        auto w  = this->sample(index) *
                  (this->range_ub - this->range_lb) + this->range_lb;
        matrix[i][c] = w;
        matrix[c][i] = -w;
    }

    // A<->A connections
    index++;
    int k = 0;
    std::vector<std::string> connections_seen;

    for (auto const &connection : this->connections)
    {
        // Get connection information
        int x1, y1, z1, x2, y2, z2;
        std::tie(x1, y1, z1, x2, y2, z2) = connection.first;

        // Find location of the two neurons in this->neurons list
        int l1 = -1;
        int l2 = -1;
        int c = 0;
        for(auto const &neuron : this->neurons)
        {
            int x, y, z;
            std::tie(x, y, z) = neuron.first;
            if (x == x1 and y == y1 and z == z1)
            {
                l1 = c;
            }
            else if (x == x2 and y == y2 and z == z2)
            {
                l2 = c;
            }
            // Update counter
            c++;
        }

        // Add connection to seen connections
        if(l1 > l2)
        {
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
            // else continue to next iteration
        else{
            continue;
        }

        // Get weight
        auto w  = this->sample(index + k) *
                  (this->range_ub - this->range_lb) + this->range_lb;

        // Set connection in weight matrix
        matrix[l1][l2] = w;
        matrix[l2][l1] = -w;
        k++;
    }

    // Update matrix
    this->ode_matrix = matrix;

    // Reset neuron state
    this->reset_neuron_state();
}


/**
 *  Set states back to original value (that is on the unit circle)
 */
void BrokenDifferentialCPG::reset_neuron_state(){
    int c = 0;
    for(auto const &neuron : this->neurons)
    {
        // Get neuron properties
        int x, y, z, frame_of_reference;
        double bias ,gain ,state;
        std::tie(x, y, z) = neuron.first;
        std::tie(bias, gain, state, frame_of_reference) = neuron.second;

        if (z == -1)
        {
            // Neuron B
            if (this->reset_neuron_random)
            {
                this->neurons[{x, y, z}] = {0.f,
                                            0.f,
                                            ((double) rand() / (RAND_MAX))*2*this->init_neuron_state - this->init_neuron_state,
                                            frame_of_reference};
            }
            else
            {
                this->neurons[{x, y, z}] = {0.f, 0.f, -this->init_neuron_state, frame_of_reference};
            }
        }
        else
        {
            // Neuron A
            if (this->reset_neuron_random)
            {
                this->neurons[{x, y, z}] = {0.f,
                                            0.f,
                                            ((double) rand() / (RAND_MAX))*2*this->init_neuron_state - this->init_neuron_state,
                                            frame_of_reference};
            }
            else
            {
                this->neurons[{x, y, z}] = {0.f, 0.f, +this->init_neuron_state, frame_of_reference};
            }
        }
        c++;
    }
}

/**
 * Step function that is called from within Update()
 *
 * @param _time
 * @param _output
 */
void BrokenDifferentialCPG::step(
        const double time,
        const double dt)
{
    int neuron_count = 0;
    for (const auto &neuron : this->neurons)
    {
        // Neuron.second accesses the second 3-tuple of a neuron, containing the bias/gain/state.
        double recipient_bias, recipient_gain, recipient_state;
        int frame_of_reference;
        std::tie(recipient_bias, recipient_gain, recipient_state, frame_of_reference) = neuron.second;

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

    double angle_difference = 0.0;
    double slow_down_factor = 1.0;
    if (use_frame_of_reference) {
        angle_difference = angle_to_target_sensor->detect_angle();
        const double frame_of_reference_slower_power = 7.0;
        slow_down_factor = std::pow(
                (180.0 - std::abs(angle_difference))/180.0, frame_of_reference_slower_power);
    }

    // Loop over all neurons to actually update their states. Note that this is a new outer for loop
    auto i = 0; auto j = 0;
    for (auto &neuron : this->neurons)
    {
        // Get bias gain and state for this neuron. Note that we don't take the coordinates.
        // However, they are implicit as their order did not change.
        double bias, gain, state;
        int frame_of_reference;
        std::tie(bias, gain, state, frame_of_reference) = neuron.second;
        double x, y, z;
        std::tie(x, y, z) = neuron.first;
        neuron.second = {bias, gain, this->next_state[i], frame_of_reference};
        j = this->motor_coordinates[{x,y}];
        // Should be one, as output should be based on +1 neurons, which are the A neurons
        if (i % 2 == 1)
        {
            // TODO: Add Milan's function here as soon as things are working a bit
            // f(a) = (w_ao*a - bias)*gain

            // Apply saturation formula
            auto x_input = this->next_state[i];

            double output_j = this->output_function(x_input);

            // Use frame of reference
            if(use_frame_of_reference and frame_of_reference != 0)
            {
                if ((frame_of_reference == 1 and angle_difference < 0) or
                    (frame_of_reference == -1 and angle_difference > 0)) //TODO >= / <= ?
                {
                    output_j *= slow_down_factor;
                    //std::cout << "Slow down " << x <<','<< y <<','<< z << " with factor " << slow_down_factor << std::endl;
                    //output_j = 0;
                }
            }

            this->output[j] = output_j;
        }
        i++;
    }
}

double BrokenDifferentialCPG::output_function(double input) const
{
    return this->signal_factor_all_
           * this->abs_output_bound
           * (
                   (2.0) / (1.0 + std::pow(2.718, -2.0 * input / this->abs_output_bound))
                   - 1
           );
}
