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
 * Author: Milan Jelisavcic
 * Date: December 29, 2018
 *
 */

#ifndef REVOLVE_DIFFERENTIALCPG_H_
#define REVOLVE_DIFFERENTIALCPG_H_

// Standard libraries
#include <map>
#include <tuple>

// External libraries
#include <eigen3/Eigen/Core>
#include <boost/numeric/odeint/stepper/runge_kutta4.hpp>

// Project headers
#include "Evaluator.h"
#include "Brain.h"
#include <revolve/gazebo/battery/Battery.h>

/// These numbers are quite arbitrary. It used to be in:13 out:8 for the
/// Arduino, but I upped them both to 20 to accommodate other scenarios.
/// Should really be enforced in the Python code, this implementation should
/// not be the limit.
#define MAX_INPUT_NEURONS 20
#define MAX_OUTPUT_NEURONS 20

/// Arbitrary value
#define MAX_HIDDEN_NEURONS 30

/// Convenience
#define MAX_NON_INPUT_NEURONS (MAX_HIDDEN_NEURONS + MAX_OUTPUT_NEURONS)

/// (bias, tau, gain) or (phase offset, period, gain)
#define MAX_NEURON_PARAMS 3

typedef std::vector< double > state_type;

namespace revolve
{
  namespace gazebo {
    class DifferentialCPG
        : public Brain
    {
      /// \brief Constructor
      /// \param[in] _modelName Name of the robot
      /// \param[in] _node The brain node
      /// \param[in] _motors Reference to a motor list, it be reordered
      /// \param[in] _sensors Reference to a sensor list, it might be reordered
      public:
      DifferentialCPG(
          const ::gazebo::physics::ModelPtr &_model,
          const sdf::ElementPtr robot_config,
          const std::vector< MotorPtr > &_motors,
          const std::vector< SensorPtr > &_sensors,
          std::shared_ptr<::revolve::gazebo::Battery> battery);

      public: void set_ode_matrix();

      /// \brief Destructor
      public: virtual ~DifferentialCPG();

      /// \brief The default update method for the controller
      /// \param[in] _motors Motor list
      /// \param[in] _sensors Sensor list
      /// \param[in] _time Current world time
      /// \param[in] _step Current time step
      public:
      virtual void Update(
          const std::vector< MotorPtr > &_motors,
          const std::vector< SensorPtr > &_sensors,
          const double _time,
          const double _step);

      protected:
      void step(
          const double _time,
          double *_output);

      /// \brief Register of motor IDs and their x,y-coordinates
      protected: std::map< std::string, std::tuple< int, int > > positions;

      public: std::map< std::tuple< int, int>, int> motor_coordinates;


        /// \brief Register of individual neurons in x,y,z-coordinates
      /// \details x,y-coordinates define position of a robot's module and
      // z-coordinate define A or B neuron (z=1 or -1 respectively). Stored
      // values are a bias, gain, state and frame of reference of each neuron.
      protected:
      std::map< std::tuple< int, int, int >, std::tuple< double, double, double, int > >
          neurons;

      /// \brief Register of connections between neighnouring neurons
      /// \details Coordinate set of two neurons (x1, y1, z1) and (x2, y2, z2)
      // define a connection. The second tuple contains 1: the connection value and
      // 2: the weight index corresponding to this connection.
      protected:
      std::map< std::tuple< int, int, int, int, int, int >, std::tuple<int, int > >
          connections;

      /// \brief Runge-Kutta 45 stepper
      protected: boost::numeric::odeint::runge_kutta4< state_type > stepper;

      /// \brief Pointer to access parameters
      private: sdf::ElementPtr learner;

      /// \brief Used to determine the next state array
      private: double *next_state;

      /// \brief Used for ODE-int
      protected: std::vector<std::vector<double>> ode_matrix;
      protected: state_type x;

      /// \brief One input state for each input neuron
      private: double *input;

      /// \brief Used to determine the output to the motors array
      private: double *output;

      /// \brief Location where to save output
      private: std::string directory_name;

      /// \brief Name of the robot
      private: ::gazebo::physics::ModelPtr robot;

      /// \brief Init BO loop
      public: void bo_init_sampling();

      /// \brief Main BO loop
      public: void bo_step();

      /// \brief evaluation rate
      private: double evaluation_rate;

      /// \brief Get fitness
      private: void save_fitness();

      /// \brief Pointer to the fitness evaluator
      protected: EvaluatorPtr evaluator;

      /// \brief Holder for BO parameters
      public: struct Params;

      /// \brief Save parameters
      private: void save_parameters();

      /// \brief Best fitness seen so far
      private: double best_fitness = -10.0;

      /// \brief Sample corresponding to best fitness
      private: Eigen::VectorXd best_sample;

      /// \brief Starting time
      private: double start_time;

      /// \brief BO attributes
      private: size_t current_iteration = 0;

      /// \brief Max number of iterations learning is allowed
      private: size_t n_learning_iterations;

      /// \brief Number of initial samples
      private: size_t n_init_samples;

      /// \brief Cool down period
      private: size_t n_cooldown_iterations;

      /// \brief Limbo optimizes in [0,1]
      private: double range_lb;

      /// \brief Limbo optimizes in [0,1]
      private: double range_ub;

      /// \brief How to take initial random samples
      private: std::string init_method;

      /// \brief All fitnesses seen so far. Called observations in limbo context
      private: std::vector< Eigen::VectorXd > observations;

      /// \brief All samples seen so far.
      private: std::vector< Eigen::VectorXd > samples;

      /// \brief The number of weights to optimize
      private: size_t n_weights;

      /// \brief Dummy evaluation funtion to reduce changes to be made on the limbo package
      public: struct evaluation_function;

      /// \brief Reset the robot to starting position each iteration.
      private: bool reset_robot_position;

      /// \brief Reset neuron state at each iteration (also during validation)
      private: bool reset_neuron_state_bool;

      /// \brief Factor to multiply output signal with
      private: double signal_factor_all_;

      /// \brief Factor to multiply output signal with
      private: double signal_factor_mid;

      /// \brief Factor to multiply output signal with
      private: double signal_factor_left_right;

      /// \brief Function that resets neuron state
      private: void reset_neuron_state();

      /// \brief When reset a neuron state,do it randomly:
      private: bool reset_neuron_random;

      /// \brief Boolean to enable/disable constructing plots
      private: bool run_analytics;

      /// \brief Automatically generate plots
      public: void get_analytics();

      /// \brief Show output (1) or not (0)
      public: int verbose;

      /// \brief Time to skip for fitness evaluation during training
      public: int startup_time;

      /// \brief Helper for startup time
      private: bool start_fitness_recording = true;

      /// \brief absolute bound on motor signal value
      public: double abs_output_bound;

      /// \brief Holds the number of motors in the robot
      private: size_t n_motors;

      /// \brief Helper for numerical integrator
      private: double previous_time = 0;

      /// \brief Initial neuron state
      private: double init_neuron_state;

      /// \brief Holder for loading a brain
      private: std::string load_brain = "";

      /// \brief Specifies the acquisition function used
      public: std::string acquisition_function;

      /// \brief Use frame of reference {-1,0,1} version or not
      private: bool use_frame_of_reference;

        // BO Learner parameters
    private: double kernel_noise_;
    private: bool kernel_optimize_noise_;
    public: double kernel_sigma_sq_;
    public: double kernel_l_;
    private: int kernel_squared_exp_ard_k_;
    private: double acqui_gpucb_delta_ ;
    public: double acqui_ucb_alpha_;
    private: double acqui_ei_jitter_;
    };
  }
}

#endif //REVOLVE_DIFFERENTIALCPG_H_
