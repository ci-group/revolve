/*
* Copyright (C) 2017 Vrije Universiteit Amsterdam
*
* Licensed under the Apache License, Version 2.0 (the "License");
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
* Description: Brain class for the default Neural Network as specified by
*              Revolve. This is loosely based on the neural network
*              code provided with the Robogen framework.
* Author: Elte Hupkes
*
*/

#ifndef REVOLVE_GAZEBO_BRAIN_NEURALNETWORK_H_
#define REVOLVE_GAZEBO_BRAIN_NEURALNETWORK_H_

#include <map>
#include <string>
#include <vector>

#include <gazebo/gazebo.hh>

#include <revolve/msgs/neural_net.pb.h>

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
  namespace gazebo
  {
    typedef const boost::shared_ptr< revolve::msgs::ModifyNeuralNetwork const >
        ConstModifyNeuralNetworkPtr;

    /// Copied from NeuronRepresentation.h
    enum neuronType
    {
      INPUT,
      SIMPLE,
      SIGMOID,
      CTRNN_SIGMOID,
      OSCILLATOR,
      SUPG
    };

    class NeuralNetwork
        : public Brain
    {
      /// \brief Constructor
      /// \param[in] _modelName Name of the robot
      /// \param[in] _node The brain node
      /// \param[in] _motors Reference to a motor list, it be reordered
      /// \param[in] _sensors Reference to a sensor list, it might be reordered
      public: NeuralNetwork(
          const ::gazebo::physics::ModelPtr &_model,
          const sdf::ElementPtr &_settings,
          const std::vector< MotorPtr > &_motors,
          const std::vector< SensorPtr > &_sensors);

      /// \brief Destructor
      public: virtual ~NeuralNetwork();

      /// \brief The default update method for the controller
      /// \param[in] _motors Motor list
      /// \param[in] _sensors Sensor list
      /// \param[in] _time Current world time
      /// \param[in] _step Current time step
      public:  virtual void Update(
          const std::vector< MotorPtr > &_motors,
          const std::vector< SensorPtr > &_sensors,
          const double _time,
          const double _step);

      /// \brief Steps the neural network
      protected: void Step(const double _time);

      /// \brief Request handler to modify the neural network
      protected: void Modify(ConstModifyNeuralNetworkPtr &_request);

      /// \brief Network modification subscriber
      protected: ::gazebo::transport::SubscriberPtr alterSub_;

      /// \brief Connection weights, separated into three arrays.
      /// \note Only output and hidden neurons are weight targets.
      /// \details Weights are stored with gaps, meaning that every neuron holds
      /// entries for the maximum possible number of connections. This makes
      /// restructuring the weights arrays when a hidden neuron is removed
      /// slightly less cumbersome.
      protected: double inputWeights_[
          MAX_INPUT_NEURONS * (MAX_OUTPUT_NEURONS + MAX_HIDDEN_NEURONS)];

      /// \brief output weights
      protected: double outputWeights_[
          MAX_OUTPUT_NEURONS * (MAX_OUTPUT_NEURONS + MAX_HIDDEN_NEURONS)];

      /// \brief hidden weights
      protected: double hiddenWeights_[
          MAX_HIDDEN_NEURONS * (MAX_OUTPUT_NEURONS + MAX_HIDDEN_NEURONS)];

      /// \brief Type of each non-input neuron
      /// \details Unlike weights, types, params and current states are stored
      /// without gaps, meaning the first `m` entries are for output neurons,
      /// followed by `n` entries for hidden neurons. If a hidden neuron is
      /// removed, the items beyond it are moved back.
      protected: unsigned int types_[(MAX_OUTPUT_NEURONS + MAX_HIDDEN_NEURONS)];

      /// \brief Params for hidden and output neurons, quantity depends on
      /// the type of neuron
      protected: double params_[
          MAX_NEURON_PARAMS * (MAX_OUTPUT_NEURONS + MAX_HIDDEN_NEURONS)];

      /// \brief Output states arrays for the current state and the next state.
      protected: double state1_[MAX_OUTPUT_NEURONS + MAX_HIDDEN_NEURONS];

      protected: double state2_[MAX_OUTPUT_NEURONS + MAX_HIDDEN_NEURONS];

      /// \brief One input state for each input neuron
      protected: double input_[MAX_INPUT_NEURONS];

      /// \brief Used to determine the current state array.
      /// \example false := state1, true := state2.
      protected: bool flipState_;

      /// \brief Stores the type of each neuron ID
      protected: std::map< std::string, std::string > layerMap_;

      /// \brief Stores the position of each neuron ID, relative to its type
      protected: std::map< std::string, unsigned int > positionMap_;

      /// \brief The number of inputs
      protected: unsigned int nInputs_;

      /// \brief The number of outputs
      protected: unsigned int nOutputs_;

      /// \brief The number of hidden units
      protected: unsigned int nHidden_;

      /// \brief The number of non-inputs (i.e. nOutputs + nHidden)
      protected: unsigned int nNonInputs_;

      /// \brief Connection helper
      private: void ConnectionHelper(
          const std::string &_src,
          const std::string &_dst,
          const double _weight);
    };
  } /* namespace gazebo */
} /* namespace revolve */

#endif /* REVOLVE_GAZEBO_BRAIN_NEURALNETWORK_H_ */
