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
#include <Eigen/Core>

// Project headers
#include "Evaluator.h"
#include "Brain.h"

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
          const sdf::ElementPtr _settings,
          const std::vector< MotorPtr > &_motors,
          const std::vector< SensorPtr > &_sensors);

      /// \brief Destructor
      public:
      virtual ~DifferentialCPG();

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
      void Step(
          const double _time,
          double *_output);

      /// \brief Register of motor IDs and their x,y-coordinates
      protected:
      std::map< std::string, std::tuple< int, int > > positions_;

      /// \brief Register of individual neurons in x,y,z-coordinates
      /// \details x,y-coordinates define position of a robot's module and
      // z-coordinate define A or B neuron (z=1 or -1 respectively). Stored
      // values are a bias, gain, state of each neuron.
      protected:
      std::map< std::tuple< int, int, int >, std::tuple< double, double, double > >
          neurons_;

      /// \brief Register of connections between neighnouring neurons
      /// \details Coordinate set of two neurons (x1, y1, z1) and (x2, y2, z2)
      // define a connection.
      protected:
      std::map< std::tuple< int, int, int, int, int, int >, double >
          connections_;

      /// \brief Used to determine the next state array
      private: double *nextState_;

      /// \brief One input state for each input neuron
      private: double *input_;

      /// \brief Used to determine the output to the motors array
      private: double *output_;

      /// \brief Name of the robot
      private:
      ::gazebo::physics::ModelPtr robot_;

      /// \brief Init BO loop
      public:
      void BO_init();

      /// \brief Main BO loop
      public:
      void BO_step();

      /// \brief evaluation rate
      private:
      double evaluationRate_;

      /// \brief Maximal number of evaluations
      private:
      size_t maxEvaluations_;

      /// \brief Get fitness
      private:
      void getFitness();

      /// \brief Pointer to the fitness evaluator
      protected:
      EvaluatorPtr evaluator;

      /// \brief Holder for BO parameters
      public:
      struct Params;

      /// \brief Best fitness seen so far
      private:
      double bestFitness;

      /// \brief Sample corresponding to best fitness
      private:
      Eigen::VectorXd bestSample;

      /// \brief
      private:
      double startTime_;

      /// \brief BO attributes
      private:
      size_t currentIteration;

      /// \brief Max number of iterations learning is allowed
      private:
      size_t maxLearningIterations;

      /// \brief Number of initial samples
      private:
      size_t nInitialSamples;

      /// \brief Cool down period
      private:
      size_t noLearningIterations;

      /// \brief Limbo optimizes in [0,1]
      private:
      double rangeLB;

      /// \brief Limbo optimizes in [0,1]
      private:
      double rangeUB;

      /// \brief How to take initial random samples
      private:
      std::string initializationMethod;

      /// \brief All fitnesses seen so far. Called observations in limbo context
      private:
      std::vector< Eigen::VectorXd > observations;

      /// \brief All samples seen so far.
      private:
      std::vector< Eigen::VectorXd > samples;

      /// \brief The number of weights to optimize
      private:
      int nWeights;

      /// \brief Dummy evaluation funtion to reduce changes to be made on the limbo package
      public:
      struct evaluationFunction;

      /// \brief Boolean to enable/disable constructing plots
      private:
      bool runAnalytics;

      /// \brief Automatically generate plots
      public:
      void getAnalytics();

      public: size_t getNWeights();

      public: double fMax;

      private: double previousTime = 0;
    };
  }
}

#endif //REVOLVE_DIFFERENTIALCPG_H_
