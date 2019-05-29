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

// STL macros
#include <cstdlib>
#include <map>
#include <algorithm>
#include <random>
#include <tuple>
#include <time.h>
#include <boost/algorithm/string/split.hpp>
#include <boost/algorithm/string/classification.hpp>

// Other libraries
#include <limbo/acqui/ucb.hpp>
#include <limbo/acqui/gp_ucb.hpp>
#include <limbo/acqui/ei.hpp>
#include <limbo/bayes_opt/bo_base.hpp>
#include <limbo/init/lhs.hpp>
#include <limbo/kernel/kernel.hpp>
#include <limbo/kernel/matern_five_halves.hpp>
#include <limbo/model/gp.hpp>
#include <limbo/mean/mean.hpp>
#include <limbo/tools/macros.hpp>
#include <limbo/opt/nlopt_no_grad.hpp>

// Project headers
#include "../motors/Motor.h"

#include "../sensors/Sensor.h"

#include "DifferentialCPG.h"

#include "DifferentialCPG_BO.h"

// TODO: Resolve odd behaviour at the end of the validation procedure
// This behaviour is not present if you directly load a trained controller

// Define namespaces
namespace gz = gazebo;
using namespace revolve::gazebo;

// Copied from the limbo tutorial the BO implementation is based on
using Mean_t = limbo::mean::Data<DifferentialCPG::Params>;
using Init_t = limbo::init::LHS<DifferentialCPG::Params>;
using Kernel_t = limbo::kernel::MaternFiveHalves<DifferentialCPG::Params>;
using GP_t = limbo::model::GP<DifferentialCPG::Params, Kernel_t, Mean_t>;

/**
 * Constructor for DifferentialCPG class.
 *
 * @param _model
 * @param robot_config
 */
DifferentialCPG::DifferentialCPG(
    const ::gazebo::physics::ModelPtr &_model,
    const sdf::ElementPtr robot_config,
    const std::vector< revolve::gazebo::MotorPtr > &_motors,
    const std::vector< revolve::gazebo::SensorPtr > &_sensors)
    : next_state(nullptr)
    , input(new double[_sensors.size()])
    , output(new double[_motors.size()])
{

  this->learner = robot_config->GetElement("rv:brain")->GetElement("rv:learner");

  // Check for brain
  if (not robot_config->HasElement("rv:brain"))
  {
    throw std::runtime_error("DifferentialCPG brain did not receive brain");
  }
  auto brain = robot_config->GetElement("rv:brain");

  // Check for learner
  if (not brain->HasElement("rv:learner"))
  {
    throw std::runtime_error("DifferentialCPG brain did not receive learner");
  }
  auto learner = brain->GetElement("rv:learner");

  // Check for controller
  if (not brain->HasElement("rv:controller"))
  {
    throw std::runtime_error("DifferentialCPG brain did not receive controller");
  }
  auto controller = brain->GetElement("rv:controller");

  // Check for actuators
  if (not brain->HasElement("rv:actuators"))
  {
    throw std::runtime_error("DifferentialCPG brain did not receive actuators");
  }
  auto actuators = brain->GetElement("rv:actuators");

  // Controller parameters
  this->reset_neuron_state_bool = std::stoi(controller->GetAttribute("reset_neuron_state_bool")->GetAsString());
  this->reset_neuron_random = std::stoi(controller->GetAttribute("reset_neuron_random")->GetAsString());
  this->init_neuron_state = std::stod(controller->GetAttribute("init_neuron_state")->GetAsString());
  this->range_lb = -std::stod(controller->GetAttribute("range_ub")->GetAsString());
  this->range_ub = std::stod(controller->GetAttribute("range_ub")->GetAsString());
  this->use_frame_of_reference = std::stoi(controller->GetAttribute("use_frame_of_reference")->GetAsString());
  this->signal_factor_all_ = std::stod(controller->GetAttribute("signal_factor_all")->GetAsString());
  this->signal_factor_mid = std::stod(controller->GetAttribute("signal_factor_mid")->GetAsString());
  this->signal_factor_left_right = std::stod(controller->GetAttribute("signal_factor_left_right")->GetAsString());

    // Limbo BO Learner parameters
    this->kernel_noise_ = std::stod(learner->GetAttribute("kernel_noise")->GetAsString());
    this->kernel_optimize_noise_ = std::stoi(learner->GetAttribute("kernel_optimize_noise")->GetAsString());
    this->kernel_sigma_sq_ = std::stod(learner->GetAttribute("kernel_sigma_sq")->GetAsString());
    this->kernel_l_ = std::stod(learner->GetAttribute("kernel_l")->GetAsString());
    this->kernel_squared_exp_ard_k_ = std::stoi(learner->GetAttribute("kernel_squared_exp_ard_k")->GetAsString());
    this->acqui_gpucb_delta_ = std::stod(learner->GetAttribute("acqui_gpucb_delta")->GetAsString());
    this->acqui_ucb_alpha_ = std::stod(learner->GetAttribute("acqui_ucb_alpha")->GetAsString());
    this->acqui_ei_jitter_ = std::stod(learner->GetAttribute("acqui_ei_jitter")->GetAsString());

    // Non-limbo BO learner para
    this->n_init_samples = std::stoi(learner->GetAttribute("n_init_samples")->GetAsString());
    this->n_learning_iterations = std::stoi(learner->GetAttribute("n_learning_iterations")->GetAsString());
    this->n_cooldown_iterations = std::stoi(learner->GetAttribute("n_cooldown_iterations")->GetAsString());
    this->init_method = learner->GetAttribute("init_method")->GetAsString();

  // Meta parameters
  this->startup_time = std::stoi(controller->GetAttribute("startup_time")->GetAsString());
  this->reset_robot_position = std::stoi(controller->GetAttribute("reset_robot_position")->GetAsString());
  this->run_analytics = std::stoi(controller->GetAttribute("run_analytics")->GetAsString());
  this->load_brain = controller->GetAttribute("load_brain")->GetAsString();
  this->evaluation_rate = std::stoi(learner->GetAttribute("evaluation_rate")->GetAsString());
  this->abs_output_bound = std::stoi(learner->GetAttribute("abs_output_bound")->GetAsString());
  this->verbose = std::stoi(controller->GetAttribute("verbose")->GetAsString());

  // Create transport node
  this->node_.reset(new gz::transport::Node());
  this->node_->Init();

  // Get Robot
  this->robot = _model;
  this->n_motors = _motors.size();
  auto name = _model->GetName();

  if(this->verbose)
  {
    std::cout << robot_config->GetDescription() << std::endl;
  }
  auto motor = actuators->HasElement("rv:servomotor")
               ? actuators->GetElement("rv:servomotor")
               : sdf::ElementPtr();
  auto j = 0;
  while(motor)
  {
    if (not motor->HasAttribute("coordinates"))
    {
      std::cerr << "Missing required motor coordinates" << std::endl;
      throw std::runtime_error("Robot brain error");
    }

    // Split string and get coordinates
    auto coordinate_string = motor->GetAttribute("coordinates")->GetAsString();
    std::vector<std::string> coordinates;
    boost::split(coordinates, coordinate_string, boost::is_any_of(";"));

    // Check if we have exactly 2 coordinates
    if (not coordinates.size() == 2)
    {
      throw std::runtime_error("Coordinates are not exactly of length two ");
    }

    // Check if the coordinates are integers
    try
    {
      for(auto coord : coordinates)
      {
        std::stoi(coord);
      }
    }
    catch(std::invalid_argument e1)
    {
      std::cout << "Invalid argument: Cannot cast coordinates to integers " << std::endl;
    };

    // Pass coordinates
    auto coord_x = std::stoi(coordinates[0]);
    auto coord_y = std::stoi(coordinates[1]);
    if (this->verbose)
    {
      std::cout << "coord_x,coord_y = " << coord_x << "," << coord_y << std::endl;
    }
    auto motor_id = motor->GetAttribute("part_id")->GetAsString();
    this->positions[motor_id] = {coord_x, coord_y};
    this->motor_coordinates[{coord_x, coord_y}] = j;

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
    this->neurons[{coord_x, coord_y, 1}] = {0.f, 0.f, this->init_neuron_state, frame_of_reference}; //Neuron A
    this->neurons[{coord_x, coord_y, -1}] = {0.f, 0.f, -this->init_neuron_state, frame_of_reference}; // Neuron B

    // TODO: Add check for duplicate coordinates
    motor = motor->GetNextElement("rv:servomotor");
    j++;
  }

  // Add connections between neighbouring neurons
  int i = 0;
  for (const auto &position : this->positions)
  {
    // Get name and x,y-coordinates of all neurons.
    auto name = position.first;
    int x, y; std::tie(x, y) = position.second;

    // Continue to next iteration in case there is already a connection between the 1 and -1 neuron.
    // These checks feel a bit redundant.
    // if A->B connection exists.
    if (this->connections.count({x, y, 1, x, y, -1}))
    {
      continue;
    }
    // if B->A connection exists:
    if (this->connections.count({x, y, -1, x, y, 1}))
    {
      continue;
    }

    // Loop over all positions. We call it neighbours, but we still need to check if they are a neighbour.
    for (const auto &neighbour : this->positions)
    {
      // Get information of this neuron (that we call neighbour).
      int near_x, near_y; std::tie(near_x, near_y) = neighbour.second;

      // If there is a node that is a Moore neighbour, we set it to be a neighbour for their A-nodes.
      // Thus the connections list only contains connections to the A-neighbourhood, and not the
      // A->B and B->A for some node (which makes sense).
      int dist_x = std::abs(x - near_x);
      int dist_y = std::abs(y - near_y);

      // TODO: Verify for non-spiders
      if (dist_x + dist_y == 2)
      {
        if(std::get<0>(this->connections[{x, y, 1, near_x, near_y, 1}]) != 1 or
           std::get<0>(this->connections[{near_x, near_y, 1, x, y, 1}]) != 1)
        {
          if(this->verbose)
          {
            std::cout << "New connection at index " << i << ": " << x << ", " << y << ", " << near_x << ", " << near_y << std::endl;
          }
          this->connections[{x, y, 1, near_x, near_y, 1}] = std::make_tuple(1, i);
          this->connections[{near_x, near_y, 1, x, y, 1}] = std::make_tuple(1, i);
          i++;
        }
      }
    }
  }

  // Create directory for output.
  this->directory_name = controller->GetAttribute("output_directory")->GetAsString();
  if(this->directory_name.empty())
  {
    this->directory_name = "output/cpg_bo/";
    this->directory_name += std::to_string(time(0)) + "/";
  }

  std::system(("mkdir -p " + this->directory_name).c_str());

  // Initialise array of neuron states for Update() method
  this->next_state = new double[this->neurons.size()];
  this->n_weights = (int)(this->connections.size()/2) + this->n_motors;

  // Check if we want to load a pre-trained brain
  if(!this->load_brain.empty())
  {
    // Get line
    if(this->verbose)
    {
      std::cout << "I will load the following brain:" << std::endl;
    }
    std::ifstream brain_file(this->load_brain);
    std::string line;
    std::getline(brain_file, line);

    // Get weights in line
    std::vector<std::string> weights;
    boost::split(weights, line, boost::is_any_of(","));

    // Save weights for brain
    Eigen::VectorXd loaded_brain(this->n_weights);
    for(size_t j = 0; j < this->n_weights; j++)
    {
      loaded_brain(j) = std::stod(weights.at(j));
      if(this->verbose)
      {
        std::cout << loaded_brain(j)  << ",";
      }
    }
    if(this->verbose)
    {
      std::cout << std::endl;
    }

    // Close brain
    brain_file.close();

    // Save these weights
    this->samples.push_back(loaded_brain);

    // Set ODE matrix at initialization
    this->set_ode_matrix();

    // Go directly into cooldown phase: Note we do require that best_sample is filled. Check this
    this->current_iteration = this->n_init_samples + this->n_learning_iterations;

    if(this->verbose)
    {
      std::cout << std::endl << "Brain has been loaded." << std::endl;
    }
  }
  else
  {
    if (this->verbose)
    {
      std::cout << "Don't load existing brain" << std::endl;
    }

    // Initialize BO
    this->bo_init_sampling();
  }

  // Initiate the cpp Evaluator
  this->evaluator.reset(new Evaluator(this->evaluation_rate));
  this->evaluator->directory_name = this->directory_name;
}

/**
 * Destructor
 */
DifferentialCPG::~DifferentialCPG()
{
  delete[] this->next_state;
  delete[] this->input;
  delete[] this->output;
}

/**
 * Dummy function for limbo
 */
struct DifferentialCPG::evaluation_function{
  // Number of input dimension (samples.size())
  BO_PARAM(size_t, dim_in, 18);

  // number of dimensions of the fitness
  BO_PARAM(size_t, dim_out, 1);

  Eigen::VectorXd operator()(const Eigen::VectorXd &x) const {
    return limbo::tools::make_vector(0);
  };
};

/**
 * Performs the initial random sampling for BO
 */
void DifferentialCPG::bo_init_sampling(){
  if(this->verbose)
  {
    // We only want to optimize the weights for now.
    std::cout << "Number of weights = connections/2 + n_motors are "
              << this->connections.size()/2
              << " + "
              << this->n_motors
              << std::endl;

    // Information purposes
    std::cout << std::endl << "Sample method: " << this->init_method << ". Initial "
                                                                        "samples are: " << std::endl;
  }

  // Random sampling
  if(this->init_method == "RS")
  {
    for (size_t i = 0; i < this->n_init_samples; i++)
    {
      // Working variable to hold a random number for each weight to be optimized
      Eigen::VectorXd init_sample(this->n_weights);

      // For all weights
      for (size_t j = 0; j < this->n_weights; j++)
      {
        // Generate a random number in [0, 1]. Transform later
        double f = ((double) rand() / (RAND_MAX));

        // Append f to vector
        init_sample(j) = f;
      }

      // Save vector in samples.
      this->samples.push_back(init_sample);
    }
  }
    // Latin Hypercube Sampling
  else if(this->init_method == "LHS")
  {
    // Working variable
    double my_range = 1.f/this->n_init_samples;

    // If we have n dimensions, create n such vectors that we will permute
    std::vector<std::vector<int>> all_dimensions;

    // Fill vectors
    for (size_t i=0; i < this->n_weights; i++)
    {
      std::vector<int> one_dimension;

      // Prepare for vector permutation
      for (size_t j = 0; j < this->n_init_samples; j++)
      {
        one_dimension.push_back(j);
      }

      // Vector permutation
      std::random_shuffle(one_dimension.begin(), one_dimension.end() );

      // Save permuted vector
      all_dimensions.push_back(one_dimension);
    }

    // For all samples
    for (size_t i = 0; i < this->n_init_samples; i++)
    {
      // Initialize Eigen::VectorXd here.
      Eigen::VectorXd init_sample(this->n_weights);

      // For all dimensions
      for (size_t j = 0; j < this->n_weights; j++)
      {
        // Take a LHS
        init_sample(j) = all_dimensions.at(j).at(i)*my_range + ((double) rand() / (RAND_MAX))*my_range;
      }

      // Append sample to samples
      this->samples.push_back(init_sample);
    }
  }
  else
  {
    std::cout << "Please provide a choice of init_method in {LHS, RS}" << std::endl;
  }

  // Print samples
  if(this->verbose)
  {
    for(auto init_sample :this->samples)
    {
      for (int h = 0; h < init_sample.size(); h++)
      {
        std::cout << init_sample(h) << ", ";
      }
      std::cout << std::endl;
    }
  }
}

/**
 * Function that obtains the current fitness by calling the evaluator and stores it
 */
void DifferentialCPG::save_fitness(){
  // Get fitness
  double fitness = this->evaluator->Fitness();

  // Save sample if it is the best seen so far
  if(fitness >this->best_fitness)
  {
    this->best_fitness = fitness;
    this->best_sample = this->samples.back();
  }

  if (this->verbose)
  {
    std::cout << "Iteration number " << this->current_iteration << " has fitness " <<
              fitness << ". Best fitness: " << this->best_fitness << std::endl;
  }

  // Limbo requires fitness value to be of type Eigen::VectorXd
  Eigen::VectorXd observation = Eigen::VectorXd(1);
  observation(0) = fitness;

  // Save fitness to std::vector. This fitness corresponds to the solution of the previous iteration
  this->observations.push_back(observation);

  // Write fitness to file
  std::ofstream fitness_file;
  fitness_file.open(this->directory_name + "fitnesses.txt", std::ios::app);
  fitness_file << fitness << std::endl;
  fitness_file.close();
}



/**
 * Struct that holds the parameters on which BO is called. This is required
 * by limbo.
 */
struct DifferentialCPG::Params{

    struct bayes_opt_boptimizer : public limbo::defaults::bayes_opt_boptimizer {
    };

    // depending on which internal optimizer we use, we need to import different parameters
#ifdef USE_NLOPT
    struct opt_nloptnograd : public limbo::defaults::opt_nloptnograd {
    };
#elif defined(USE_LIBCMAES)
    struct opt_cmaes : public lm::defaults::opt_cmaes {
    };
#else
#error(NO SOLVER IS DEFINED)
#endif
    struct kernel : public limbo::defaults::kernel {
        BO_PARAM(double, noise, 0.001);
        BO_PARAM(bool, optimize_noise, false);
    };

    struct bayes_opt_bobase : public limbo::defaults::bayes_opt_bobase {
        // set stats_enabled to prevent creating all the directories
        BO_PARAM(bool, stats_enabled, false);
        BO_PARAM(bool, bounded, true);
    };

    // 1 Iteration as we will perform limbo step by steop
    struct stop_maxiterations : public limbo::defaults::stop_maxiterations {
        BO_PARAM(int, iterations, 1);
    };

    struct kernel_exp : public limbo::defaults::kernel_exp {
        /// @ingroup kernel_defaults
        BO_PARAM(double, sigma_sq, 0.1);
        BO_PARAM(double, l, 0.1); // the width of the kernel. Note that it assumes equally sized ranges over dimensions
    };

    struct kernel_squared_exp_ard : public limbo::defaults::kernel_squared_exp_ard {
        /// @ingroup kernel_defaults
        BO_PARAM(int, k, 3); // k number of columns used to compute M
        /// @ingroup kernel_defaults
        BO_PARAM(double, sigma_sq, 0.1); //brochu2010tutorial p.9 without sigma_sq
    };

    struct kernel_maternfivehalves : public limbo::defaults::kernel_maternfivehalves
    {
        BO_DYN_PARAM(double, sigma_sq); //brochu2010tutorial p.9 without sigma_sq
        BO_DYN_PARAM(double, l); //characteristic length scale
    };

    struct acqui_gpucb : public limbo::defaults::acqui_gpucb {
        //UCB(x) = \mu(x) + \kappa \sigma(x).
        BO_PARAM(double, delta, 0.1 );//acqui_gpucb_delta_); // default delta = 0.1, delta in (0,1) convergence guaranteed
    };

    struct acqui_ei : public limbo::defaults::acqui_ei{
        BO_PARAM(double, jitter, 0.5);
    };

    // This is just a placeholder to be able to use limbo with revolve
    struct init_lhs : public limbo::defaults::init_lhs{
        BO_PARAM(int, samples, 0);
    };

    struct acqui_ucb : public limbo::defaults::acqui_ucb {
        //constexpr double ra = acqui_ucb_alpha_;
        //UCB(x) = \mu(x) + \alpha \sigma(x). high alpha have high exploration
        //iterations is high, alpha can be low for high accuracy in enough iterations.
        // In contrast, the lsow iterations should have high alpha for high
        // searching in limited iterations, which guarantee to optimal.
        //        BO_PARAM(double, alpha, transform_double(acqui_ucb_alpha_)); // default alpha = 0.5
        BO_DYN_PARAM(double, alpha); // default alpha = 0.5

    };
};

BO_DECLARE_DYN_PARAM(double, DifferentialCPG::Params::acqui_ucb, alpha);
BO_DECLARE_DYN_PARAM(double, DifferentialCPG::Params::kernel_maternfivehalves, sigma_sq);
BO_DECLARE_DYN_PARAM(double, DifferentialCPG::Params::kernel_maternfivehalves, l);

/**
 * Wrapper function that makes calls to limbo to solve the current BO
 * iteration and returns the best sample
 */
void DifferentialCPG::bo_step(){
    Params::acqui_ucb::set_alpha(this->acqui_ucb_alpha_);
    Params::kernel_maternfivehalves::set_l(this->kernel_l_);
    Params::kernel_maternfivehalves::set_sigma_sq(this->kernel_sigma_sq_);

    // Save all parameters once
    if (this->current_iteration == 0)
    {
        // Save parameters
        this->save_parameters();
    }
    Eigen::VectorXd x;

  // In case we are done with the initial random sampling.
  if (this->current_iteration >= this->n_init_samples)
  {
      // std::cout << "Acquisition function:  " << this->acquisition_function << std::endl;
    if(true)
    {

      // Specify bayesian optimizer. TODO: Make attribute and initialize at bo_init
      limbo::bayes_opt::BOptimizer<Params,
          limbo::initfun<Init_t>,
          limbo::modelfun<GP_t>,
          limbo::acquifun<limbo::acqui::UCB<DifferentialCPG::Params, GP_t>>> boptimizer;

      // Optimize. Pass dummy evaluation function and observations .
      boptimizer.optimize(DifferentialCPG::evaluation_function(),
                          this->samples,
                          this->observations);
      x = boptimizer.last_sample();

        // Write parametesr to verify thread-stability after the run
        std::ofstream dyn_parameters_file;
        dyn_parameters_file.open(this->directory_name + "dynamic_parameters.txt", std::ios::app);
        dyn_parameters_file << Params::acqui_ucb::alpha() << ",";
        dyn_parameters_file << Params::kernel_maternfivehalves::sigma_sq() << ",";
        dyn_parameters_file << Params::kernel_maternfivehalves::l() << std::endl;
        dyn_parameters_file.close();


    }
      //        else if(this->acquisition_function == "GP_UCB")
      //        {
      //            // Specify bayesian optimizer. TODO: Make attribute and initialize at bo_init
      //            limbo::bayes_opt::BOptimizer<Params,
      //                    limbo::initfun<Init_t>,
      //                    limbo::modelfun<GP_t>,
      //                    limbo::acquifun<limbo::acqui::GP_UCB<DifferentialCPG::Params, GP_t>>> boptimizer;
      //
      //            // Optimize. Pass dummy evaluation function and observations .
      //            boptimizer.optimize(DifferentialCPG::evaluation_function(),
      //                                this->samples,
      //                                this->observations);
      //            x = boptimizer.last_sample();
      //        }
      //        else if(this->acquisition_function == "EI")
      //        {
      //            // Specify bayesian optimizer. TODO: Make attribute and initialize at bo_init
      //            limbo::bayes_opt::BOptimizer<Params,
      //                    limbo::initfun<Init_t>,
      //                    limbo::modelfun<GP_t>,
      //                    limbo::acquifun<limbo::acqui::EI<DifferentialCPG::Params, GP_t>>> boptimizer;
      //
      //            // Optimize. Pass dummy evaluation function and observations .
      //            boptimizer.optimize(DifferentialCPG::evaluation_function(),
      //                                this->samples,
      //                                this->observations);
      //            x = boptimizer.last_sample();
      //        }
    else
    {
      std::cout << "Specify correct acquisition function: {EI, UCB, GP_UCB}" << std::endl;
    }

    // Save this x_hat_star
    this->samples.push_back(x);
  }
}

/**
 * Callback function that defines the movement of the robot
 *
 * @param _motors
 * @param _sensors
 * @param _time
 * @param _step
 */
void DifferentialCPG::Update(
    const std::vector< revolve::gazebo::MotorPtr > &_motors,
    const std::vector< revolve::gazebo::SensorPtr > &_sensors,
    const double _time,
    const double _step)
{
  // Prevent two threads from accessing the same resource at the same time
  boost::mutex::scoped_lock lock(this->networkMutex_);

  // Read sensor data and feed the neural network
  unsigned int p = 0;
  for (const auto &sensor : _sensors)
  {
    sensor->Read(this->input + p);
    p += sensor->Inputs();
  }

  this->evaluator->Update(this->robot->WorldPose(), _time, _step);

  // Only start recording the fitness after the startup time each iteration
  double elapsed_evaluation_time = _time - this->start_time;
  if((std::fmod(elapsed_evaluation_time, (int)this->evaluation_rate) >= this->startup_time) & this->start_fitness_recording)
  {
    // Update position
//    this->evaluator->Update(this->robot->WorldPose(), _time, _step);
    this->start_fitness_recording = false;
  }
  // Evaluate policy on certain time limit, or if we just started
  if ((elapsed_evaluation_time > this->evaluation_rate) or ((_time - _step) < 0.001))
  {
    // Update position
//    this->evaluator->Update(this->robot->WorldPose(), _time, _step);
    this->start_fitness_recording = true;

    // Get and save fitness (but not at start)
    if(not (_time - _step < 0.001 ))
    {
      this->save_fitness();
    }

    // Reset robot if opted to do
    if(this->reset_robot_position)
    {
      //this->robot->Reset();
      this->robot->ResetPhysicsStates();
      auto start_pose = ::ignition::math::Pose3d();
      start_pose.Set(0.0, 0.0, 0.05, 0.0, 0.0, 0.0);
      this->robot->SetWorldPose(start_pose);
      this->robot->Update();
    }

    // Reset neuron state if opted to do
    if(this->reset_neuron_state_bool)
    {
      this->reset_neuron_state();
    }

    // If we are still learning
    if(this->current_iteration < this->n_init_samples + this->n_learning_iterations)
    {
      if(this->verbose)
      {
        if (this->current_iteration < this->n_init_samples)
        {
          std::cout << std::endl << "Evaluating initial random sample" << std::endl;
        }
        else
        {
          std::cout << std::endl << "I am learning " << std::endl;
        }
      }
      // Get new sample (weights) and add sample
      this->bo_step();

      // Set new weights
      this->set_ode_matrix();

      // Update position
//      this->evaluator->Update(this->robot->WorldPose(), _time, _step);
    }
      // If we are finished learning but are cooling down - reset once
    else if((this->current_iteration >= (this->n_init_samples +
                                         this->n_learning_iterations))
            and (this->current_iteration < (this->n_init_samples +
                                            this->n_learning_iterations +
                                            this->n_cooldown_iterations - 1)))
    {
      if(this->verbose)
      {
        std::cout << std::endl << "I am cooling down " << std::endl;
      }

      // Update robot position
//      this->evaluator->Update(this->robot->WorldPose(), _time, _step);

      // Use best sample in next iteration
      this->samples.push_back(this->best_sample);

      // Set ODE matrix
      this->set_ode_matrix();
    }
      // Else we don't want to update anything, but construct plots from this run once.
    else
    {
//      // Create plots
//      if(this->run_analytics)
//      {
//        // Construct plots
//        this->get_analytics();
//      }

      // Exit
      if(this->verbose)
      {
        std::cout << std::endl << "I am finished " << std::endl;
      }
      std::exit(0);
    }

    // Evaluation policy here
    this->start_time = _time;
    this->evaluator->Reset();
    this->current_iteration += 1;
  }

  // Send new signals to the motors
  this->step(_time, this->output);
  p = 0;
  for (const auto &motor: _motors)
  {
    motor->Update(this->output + p, _step);
    p += motor->Outputs();
  }
}

/**
 * Make matrix of weights A as defined in dx/dt = Ax.
 * Element (i,j) specifies weight from neuron i to neuron j in the system of ODEs
 */
void DifferentialCPG::set_ode_matrix(){
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
    auto w  = this->samples.at(this->current_iteration)(index) *
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
    int l1, l2;
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
    auto w  = this->samples.at(this->current_iteration)(index + k) *
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

  // Save this sample to file
  std::ofstream samples_file;
  samples_file.open(this->directory_name  + "samples.txt", std::ios::app);
  auto sample = this->samples.at(this->current_iteration);
  for(size_t j = 0; j < this->n_weights; j++)
  {
    samples_file << sample(j) << ", ";
  }
  samples_file << std::endl;
  samples_file.close();
}


/**
 *  Set states back to original value (that is on the unit circle)
 */
void DifferentialCPG::reset_neuron_state(){
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
void DifferentialCPG::step(
    const double _time,
    double *_output)
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

  // Stepper. The result is saved in x. Begin time t, time step dt
  double dt = (_time - this->previous_time);
  this->previous_time = _time;

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
      _time,
      dt);

  // Copy values into nextstate
  for (size_t i = 0; i < this->neurons.size(); i++)
  {
    this->next_state[i] = x[i];
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
      auto x = this->next_state[i];

      // Use frame of reference
      if(use_frame_of_reference)
      {

        if (std::abs(frame_of_reference) == 1)
        {
          this->output[j] = this->signal_factor_left_right*this->abs_output_bound*((2.0)/(1.0 + std::pow(2.718, -2.0*x/this->abs_output_bound)) -1);
        }
        else if (frame_of_reference == 0)
        {
          this->output[j] = this->signal_factor_mid*this->abs_output_bound*((2.0)/(1.0 + std::pow(2.718, -2.0*x/this->abs_output_bound)) -1);
        }
        else
        {
          std::cout << "WARNING: frame_of_reference not in {-1,0,1}." << std::endl;
        }

      }
      // Don't use frame of reference
      else{
        this->output[j] = this->signal_factor_all_*this->abs_output_bound*((2.0)/(1.0 + std::pow(2.718, -2.0*x/this->abs_output_bound)) -1);
      }
    }
    i++;
  }

  // Comment to save disk space
//  // Write state to file
//  std::ofstream state_file;
//  state_file.open(this->directory_name + "states.txt", std::ios::app);
//  for(size_t i = 0; i < this->neurons.size(); i++)
//  {
//    state_file << this->next_state[i] << ",";
//  }
//  state_file << std::endl;
//  state_file.close();
//
//  // Write signal to file
//  std::ofstream signal_file;
//  signal_file.open(this->directory_name + "signal.txt", std::ios::app);
//  for(size_t i = 0; i < this->n_motors; i++)
//  {
//    signal_file << this->output[i] << ",";
//  }
//  signal_file << std::endl;
//  signal_file.close();
}


/**
 * Save the parameters used in this run to a file.
 */
void DifferentialCPG::save_parameters(){
  // Write parameters to file
  std::ofstream parameters_file;
  parameters_file.open(this->directory_name + "parameters.txt");

  // Various parameters
  parameters_file << "Dimensions: " << this->n_weights << std::endl;
  parameters_file << "n_init_samples: " << this->n_init_samples << std::endl;
  parameters_file << "n_learning_iterations: " << this->n_learning_iterations << std::endl;
  parameters_file << "n_cooldown_iterations: " << this->n_cooldown_iterations << std::endl;
  parameters_file << "evaluation_rate: " << this->evaluation_rate << std::endl;
  parameters_file << "abs_output_bound: " << this->abs_output_bound << std::endl;
  parameters_file << "signal_factor_all: " << this->signal_factor_all_ << std::endl;
  parameters_file << "range_lb: " << this->range_lb << std::endl;
  parameters_file << "range_ub: " << this->range_ub << std::endl;
  parameters_file << "run_analytics: " << this->run_analytics << std::endl;
  parameters_file << "load_brain: " << this->load_brain << std::endl;
  parameters_file << "reset_robot_position: " << this->reset_robot_position << std::endl;
  parameters_file << "reset_neuron_state_bool: " << this->reset_neuron_state_bool << std::endl;
  parameters_file << "reset_neuron_random: " << this->reset_neuron_random << std::endl;
  parameters_file << "initial state value: " << this->init_neuron_state << std::endl;

  // BO hyper-parameters
  parameters_file << std::endl << "Initialization method used: " << this->init_method << std::endl;
  parameters_file << "Acqui. function used: " << this->acquisition_function << std::endl;
  parameters_file << "EI jitter: " <<Params::acqui_ei::jitter() << std::endl;
  parameters_file << "UCB alpha: " << Params::acqui_ucb::alpha() << std::endl;
  parameters_file << "GP-UCB delta: " << Params::acqui_gpucb::delta() << std::endl;
  parameters_file << "Kernel noise: " << Params::kernel::noise() << std::endl;
  parameters_file << "No. of iterations: " << Params::stop_maxiterations::iterations() << std::endl;
  parameters_file << "EXP Kernel l: " << Params::kernel_exp::l() << std::endl;
  parameters_file << "EXP Kernel sigma_sq: " << Params::kernel_exp::sigma_sq()<< std::endl;
  parameters_file << "EXP-ARD Kernel k: "<< Params::kernel_squared_exp_ard::k() << std::endl;
  parameters_file << "EXP-ARD Kernel sigma_sq: "<< Params::kernel_squared_exp_ard::sigma_sq() << std::endl;
  parameters_file << "MFH Kernel sigma_sq: "<< Params::kernel_maternfivehalves::sigma_sq() << std::endl;
  parameters_file << "MFH Kernel l: "<< Params::kernel_maternfivehalves::l() << std::endl << std::endl;
  parameters_file.close();
}

/**
 * Function that automatically creates plots of the fitness, saves the best brain,
 * and saves all brains. Calls the Python file RunAnalysiBO.py
 *
 * @param _time
 * @param _output
 */
void DifferentialCPG::get_analytics(){
  // Call python file to construct plots
  std::string plot_command = "experiments/bo_learner/RunAnalysisBO.py "
                             + this->directory_name
                             + " "
                             + std::to_string((int)this->n_init_samples)
                             + " "
                             + std::to_string((int)this->n_cooldown_iterations);

  // Execute python command
  std::system(std::string("python3 " + plot_command).c_str());
}
