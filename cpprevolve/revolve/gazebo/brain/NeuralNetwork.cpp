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
* Description: TODO: <Add brief description about file purpose>
* Author: Elte Hupkes
*
*/

#include <algorithm>
#include <cmath>
#include <cstring>
#include <iostream>
#include <map>
#include <set>
#include <sstream>
#include <string>
#include <vector>

#include "NeuralNetwork.h"
#include "../motors/Motor.h"
#include "../sensors/Sensor.h"

namespace gz = gazebo;

using namespace revolve::gazebo;

/// Internal helper function to build neuron params
/////////////////////////////////////////////////
void neuronHelper(
    double *params,
    unsigned int *types,
    sdf::ElementPtr neuron);

/////////////////////////////////////////////////
void neuronHelper(
    double *params,
    unsigned int *types,
    const revolve::msgs::Neuron &neuron);

/////////////////////////////////////////////////
NeuralNetwork::NeuralNetwork(
    const ::gazebo::physics::ModelPtr &_model,
    const sdf::ElementPtr &_node,
    const std::vector< MotorPtr > &_motors,
    const std::vector< SensorPtr > &_sensors)
    : flipState_(false)
    , nInputs_(0)
    , nOutputs_(0)
    , nHidden_(0)
    , nNonInputs_(0)
{
  // Create transport node
  node_.reset(new gz::transport::Node());
  node_->Init();

  auto name = _model->GetName();
  // Listen to network modification requests
  alterSub_ = node_->Subscribe(
      "~/" + name + "/modify_neural_network", &NeuralNetwork::Modify,
      this);

  // Initialize weights, input and states to zero by default
  std::memset(inputWeights_, 0, sizeof(inputWeights_));
  std::memset(outputWeights_, 0, sizeof(outputWeights_));
  std::memset(hiddenWeights_, 0, sizeof(hiddenWeights_));
  std::memset(state1_, 0, sizeof(state1_));
  std::memset(state2_, 0, sizeof(state2_));
  std::memset(input_, 0, sizeof(input_));

  // We now setup the neural network and its parameters. The end result
  // of this operation should be that we can iterate/update all sensors in
  // a straightforward manner, likewise for the motors. We therefore first
  // create a map of all neurons, telling us how many there are for each
  // type, and what their properties are. We then iterate all sensors and
  // motors, creating the adequate neurons in place as we do so.

  // Map of ID to neuron element
  std::map< std::string, sdf::ElementPtr > neuronMap;

  // List of all hidden neurons for convenience
  std::vector< std::string > hiddenNeurons;

  // Set for tracking all collected input/output neurons
  std::set< std::string > toProcess;

  // Fetch the first neuron; note the HasElement call is necessary to
  // prevent SDF from complaining if no neurons are present.
  auto neuron = _node->HasElement("rv:neuron")
                ? _node->GetElement("rv:neuron")
                : sdf::ElementPtr();
  while (neuron)
  {
    if (not neuron->HasAttribute("layer") or not neuron->HasAttribute("id"))
    {
      std::cerr << "Missing required neuron attributes (id or layer). '"
                << std::endl;
      throw std::runtime_error("Robot brain error");
    }
    auto layer = neuron->GetAttribute("layer")->GetAsString();
    auto neuronId = neuron->GetAttribute("id")->GetAsString();

    if (layerMap_.count(neuronId))
    {
      std::cerr << "Duplicate neuron ID '" << neuronId << "'" << std::endl;
      throw std::runtime_error("Robot brain error");
    }

    layerMap_[neuronId] = layer;
    neuronMap[neuronId] = neuron;

    if ("input" == layer)
    {
      if (nInputs_ >= MAX_INPUT_NEURONS)
      {
        std::cerr << "The number of input neurons(" << (nInputs_ + 1)
                  << ") is greater than the maximum allowed one ("
                  << MAX_INPUT_NEURONS << ")" << std::endl;
        throw std::runtime_error("Robot brain error");
      }

      toProcess.insert(neuronId);
      nInputs_++;
    }
    else if ("output" == layer)
    {
      if (nOutputs_ >= MAX_OUTPUT_NEURONS)
      {
        std::cerr << "The number of output neurons(" << (nOutputs_ + 1)
                  << ") is greater than the maximum allowed  ("
                  << MAX_OUTPUT_NEURONS << ")"<< std::endl;
        throw std::runtime_error("Robot brain error");
      }

      toProcess.insert(neuronId);
      nOutputs_++;
    }
    else if ("hidden" == layer)
    {
      if (hiddenNeurons.size() >= MAX_HIDDEN_NEURONS)
      {
        std::cerr << "The number of hidden neurons("
                  << (hiddenNeurons.size() + 1)
                  << ") is greater than the maximum allowed one ("
                  << MAX_HIDDEN_NEURONS << ")" << std::endl;
        throw std::runtime_error("Robot brain error");
      }

      hiddenNeurons.push_back(neuronId);
      nHidden_++;
    }
    else
    {
      std::cerr << "Unknown neuron layer '" << layer << "'." << std::endl;
      throw std::runtime_error("Robot brain error");
    }

    neuron = neuron->GetNextElement("rv:neuron");
  }

  // Create motor output neurons at the correct position
  // We iterate a part's motors and just assign every
  // neuron we find in order.
  std::map< std::string, unsigned int > outputCountMap;
  unsigned int outPos = 0;
  for (const auto &motor : _motors)
  {
    auto partId = motor->PartId();
    if (not outputCountMap.count(partId))
    {
      outputCountMap[partId] = 0;
    }

    for (unsigned int i = 0, l = motor->Outputs(); i < l; ++i)
    {
      std::stringstream neuronId;
      neuronId << partId << "-out-" << outputCountMap[partId];
      outputCountMap[partId]++;

      auto details = neuronMap.find(neuronId.str());
      if (details == neuronMap.end())
      {
        std::cerr << "Required output neuron " << neuronId.str()
                  << " for motor could not be located" << std::endl;
        throw std::runtime_error("Robot brain error");
      }

      neuronHelper(&params_[outPos * MAX_NEURON_PARAMS],
                   &types_[outPos],
                   details->second);
      positionMap_[neuronId.str()] = outPos;
      toProcess.erase(neuronId.str());
      outPos++;
    }
  }

  // Create sensor input neurons
  std::map< std::string, unsigned int > inputCountMap;
  unsigned int inPos = 0;
  for (const auto &sensor : _sensors)
  {
    auto partId = sensor->PartId();

    if (not inputCountMap.count(partId))
    {
      inputCountMap[partId] = 0;
    }

    for (unsigned int i = 0, l = sensor->Inputs(); i < l; ++i)
    {
      std::stringstream neuronId;
      neuronId << partId << "-in-" << inputCountMap[partId];
      inputCountMap[partId]++;

      auto details = neuronMap.find(neuronId.str());
      if (details == neuronMap.end())
      {
        std::cerr << "Required input neuron " << neuronId.str()
                  << " for sensor could not be located" << std::endl;
        throw std::runtime_error("Robot brain error");
      }

      // Input neurons can currently not have a type, so
      // there is no need to process it.
      positionMap_[neuronId.str()] = inPos;
      toProcess.erase(neuronId.str());
      inPos++;
    }
  }

  // Check if there are any input / output neurons which have not
  // yet been processed. This is an error - every input / output
  // neuron should be connected to at least a virtual motor / sensor.
  if (toProcess.size())
  {
    std::cerr << "The following input / output neurons were"
        " defined, but not attached to any sensor / motor:" << std::endl;

    for (auto it = toProcess.begin(); it not_eq toProcess.end(); ++it)
    {
      std::cerr << (*it) << std::endl;
    }

    std::cerr << "Create virtual sensor and motors for input / output"
        " neurons that you would like to control manually.";
    throw std::runtime_error("Robot brain error");
  }

  // Add hidden neurons
  outPos = 0;
  for (const auto &neuronId : hiddenNeurons)
  {
    // Position relative to hidden neurons
    positionMap_[neuronId] = outPos;

    // Offset with output neurons within params / types
    auto pos = nOutputs_ + outPos;
    neuronHelper(&params_[pos * MAX_NEURON_PARAMS],
                 &types_[pos],
                 neuronMap[neuronId]);
    outPos++;
  }

  // Decode connections
  nNonInputs_ = nOutputs_ + nHidden_;
  auto connection = _node->HasElement("rv:neural_connection")
                    ? _node->GetElement("rv:neural_connection")
                    : sdf::ElementPtr();
  while (connection)
  {
    if (not connection->HasAttribute("src") or not connection
        ->HasAttribute("dst") or not connection->HasAttribute("weight"))
    {
      std::cerr << "Missing required connection attributes (`src`, `dst` "
          "or `weight`)." << std::endl;
      throw std::runtime_error("Robot brain error");
    }

    auto src = connection->GetAttribute("src")->GetAsString();
    auto dst = connection->GetAttribute("dst")->GetAsString();
    double weight;
    connection->GetAttribute("weight")->Get(weight);

    // Use connection helper to set the weight
    ConnectionHelper(src, dst, weight);

    // Load the next connection
    connection = connection->GetNextElement("rv:neural_connection");
  }
}

/////////////////////////////////////////////////
NeuralNetwork::~NeuralNetwork() = default;

/////////////////////////////////////////////////
void NeuralNetwork::Step(const double _time)
{
  unsigned int i = 0;
  unsigned int j = 0;

  if (nOutputs_ == 0)
  {
    return;
  }

  double *curState, *nextState;
  if (flipState_)
  {
    curState = state2_;
    nextState = state1_;
  }
  else
  {
    curState = state1_;
    nextState = state2_;
  }


  unsigned int maxNonInputs = MAX_HIDDEN_NEURONS + MAX_OUTPUT_NEURONS;
  for (i = 0; i < nNonInputs_; ++i)
  {
    double curNeuronActivation = 0;

    // Add input neuron values
    for (j = 0; j < nInputs_; ++j)
    {
      curNeuronActivation += inputWeights_[maxNonInputs * j + i] * input_[j];
    }

    // Add output neuron values
    for (j = 0; j < nOutputs_; ++j)
    {
      curNeuronActivation += outputWeights_[maxNonInputs * j + i] * curState[j];
    }

    // Add hidden neuron values
    for (j = 0; j < nHidden_; ++j)
    {
      curNeuronActivation +=
          hiddenWeights_[maxNonInputs * j + i] * curState[nOutputs_ + j];
    }

    unsigned int base = MAX_NEURON_PARAMS * i;
    switch (types_[i])
    {
      case SIGMOID:
        /* params are bias, gain */
        curNeuronActivation -= params_[base];
        nextState[i] =
            1.0 / (1.0 + exp(-params_[base + 1] * curNeuronActivation));
        break;
      case SIMPLE:
        /* linear, params are bias, gain */
        curNeuronActivation -= params_[base];
        nextState[i] = params_[base + 1] * curNeuronActivation;
        break;
      case OSCILLATOR:
      { // Use the block to prevent "crosses initialization" error
        /* params are period, phase offset, gain (amplitude) */
        double period = params_[base];
        double phaseOffset = params_[base + 1];
        double gain = params_[base + 2];

        /* Value in [0, 1] */
        nextState[i] =((sin((2.0 * M_PI / period) *
                            (_time - period * phaseOffset))) + 1.0) / 2.0;

        /* set output to be in [0.5 - gain/2, 0.5 + gain/2] */
        nextState[i] = (0.5 - (gain / 2.0) + nextState[i] * gain);
      }
        break;
      default:
        // Unsupported type should never happen
        std::cerr << "Invalid neuron type during processing, must be a bug."
                  << std::endl;
        throw std::runtime_error("Robot brain error");
    }
  }

  flipState_ = not flipState_;
}

/////////////////////////////////////////////////
void NeuralNetwork::Update(
    const std::vector< MotorPtr > &_motors,
    const std::vector< SensorPtr > &_sensors,
    const double _time,
    const double _step)
{
  boost::mutex::scoped_lock lock(networkMutex_);

  // Read sensor data and feed the neural network
  unsigned int p = 0;
  for (const auto &sensor : _sensors)
  {
    sensor->Read(&input_[p]);
    p += sensor->Inputs();
  }

  this->Step(_time);

  // Since the output neurons are the first in the state
  // array we can just use it to update the motors directly.
  auto output = flipState_ ? &state2_[0] : &state1_[0];

  // Send new signals to the motors
  p = 0;
  for (const auto &motor: _motors)
  {
    motor->Update(&output[p], _step);
    p += motor->Outputs();
  }
}

/////////////////////////////////////////////////
void NeuralNetwork::Modify(ConstModifyNeuralNetworkPtr &_request)
{
  boost::mutex::scoped_lock lock(networkMutex_);

  unsigned int i, j;
  for (i = 0; i < (unsigned int)_request->remove_hidden_size(); ++i)
  {
    // Find the neuron + position
    auto id = _request->remove_hidden(i);
    if (not positionMap_.count(id))
    {
      std::cerr << "Unknown neuron ID `" << id << "`" << std::endl;
      throw std::runtime_error("Robot brain error");
    }

    if ("hidden" not_eq layerMap_[id])
    {
      std::cerr
          << "Cannot remove neuron ID `"
          << id
          << "`, it is not a hidden neuron."
          << std::endl;
      throw std::runtime_error("Robot brain error");
    }

    auto pos = positionMap_[id];
    positionMap_.erase(id);
    layerMap_.erase(id);

    // Shift types
    auto s = sizeof(types_[0]);
    std::memmove(
        // Position shifted one type to the left
        types_ + (pos + nOutputs_) * s,

        // Position of next neuron type
        types_ + (pos + nOutputs_ + 1) * s,

        // # of hidden neurons beyond this one
        s * (nHidden_ - pos - 1));

    // Shift parameters
    s = sizeof(params_[0]);
    std::memmove(
        // Position of item to remove
        params_ + (pos + nOutputs_) * MAX_NEURON_PARAMS * s,

        // Position of next neuron type
        params_ + (pos + nOutputs_ + 1) * MAX_NEURON_PARAMS * s,

        // # of hidden neurons beyond this one
        (nHidden_ - pos - 1) * MAX_NEURON_PARAMS * s);

    // Reposition items in weight arrays. We start with the weights of
    // connections pointing *to* the neuron to be removed. For each entry in
    // each of the three weights arrays we have to move all hidden connection
    // weights down, then zero out the last entry
    s = sizeof(inputWeights_[0]);
    double *weightArrays[] = {
        inputWeights_,
        outputWeights_,
        hiddenWeights_
    };
    unsigned int sizes[] = {
        nInputs_,
        nOutputs_,
        nHidden_
    };

    for (size_t k = 0; k < 3; ++k)
    {
      auto weights = weightArrays[k];
      auto size = sizes[k];

      for (j = 0; j < size; ++j)
      {
        std::memmove(
            // Position of item to remove
            weights + (nOutputs_ + pos) * s,

            // Position of next item
            weights + (nOutputs_ + pos + 1) * s,

            // # of possible hidden neurons beyond this one
            (MAX_HIDDEN_NEURONS - pos - 1) * s);

        // Zero out the last item in case a connection that corresponds to it
        // is ever added.
        weights[nOutputs_ + pos] = 0;
      }
    }

    // Now the weights where the removed neuron is the source. The block of
    // weights corresponding to the neuron that is being removed needs to be
    // removed by shifting down all items beyond it.
    std::memmove(
        // Position of the item to remove
        hiddenWeights_ + pos * MAX_NON_INPUT_NEURONS * s,

        // Position of the next item
        hiddenWeights_ + (pos + 1) * MAX_NON_INPUT_NEURONS * s,

        // Remaining number of memory items
        (MAX_HIDDEN_NEURONS - pos - 1) * MAX_NON_INPUT_NEURONS * s);

    // Zero the remaining entries at the end
    std::memset(hiddenWeights_ + (MAX_HIDDEN_NEURONS - 1) * s,
           0,
           MAX_NON_INPUT_NEURONS * s);

    // Decrement the entry in the `positionMap` for all hidden neurons above
    // this one.
    for (auto iter = positionMap_.begin();
         iter not_eq positionMap_.end(); ++iter)
    {
      auto layer = layerMap_[iter->first];
      if ("hidden" == layer and positionMap_[iter->first] > pos)
      {
        positionMap_[iter->first]--;
      }
    }

    nHidden_--;
    nNonInputs_--;
  }

  // Add new requested hidden neurons
  for (i = 0; i < (unsigned int)_request->add_hidden_size(); ++i)
  {
    if (nHidden_ >= MAX_HIDDEN_NEURONS)
    {
      std::cerr
          << "Cannot add hidden neuron; the max ("
          << MAX_HIDDEN_NEURONS
          << ") is already reached."
          << std::endl;
      throw std::runtime_error("Robot brain error");
    }

    auto neuron = _request->add_hidden(i);
    const auto id = neuron.id();
    if (layerMap_.count(id))
    {
      std::cerr << "Adding duplicate neuron ID `" << id << "`" << std::endl;
      throw std::runtime_error("Robot brain error");
    }

    positionMap_[id] = nHidden_;
    layerMap_[id] = "hidden";

    unsigned int pos = nOutputs_ + nHidden_;
    neuronHelper(&params_[pos * MAX_NEURON_PARAMS], &types_[pos], neuron);
    nHidden_++;
    nNonInputs_++;
  }

  // Update parameters of existing neurons
  for (i = 0; i < (unsigned int)_request->set_parameters_size(); ++i)
  {
    auto neuron = _request->set_parameters(i);
    const auto id = neuron.id();
    if (not positionMap_.count(id))
    {
      std::cerr << "Unknown neuron ID `" << id << "`" << std::endl;
      throw std::runtime_error("Robot brain error");
    }

    auto pos = positionMap_[id];
    auto layer = layerMap_[id];

    if ("input" == layer)
    {
      std::cerr << "Input neurons cannot be modified." << std::endl;
      throw std::runtime_error("Robot brain error");
    }

    neuronHelper(&params_[pos * MAX_NEURON_PARAMS], &types_[pos], neuron);
  }

  // Set weights of new or existing connections
  for (i = 0; i < (unsigned int)_request->set_weights_size(); ++i)
  {
    auto conn = _request->set_weights(i);
    const auto src = conn.src();
    const auto dst = conn.dst();
    this->ConnectionHelper(src, dst, conn.weight());
  }
}

/////////////////////////////////////////////////
void NeuralNetwork::ConnectionHelper(
    const std::string &_src,
    const std::string &_dst,
    const double _weight)
{
  if (not layerMap_.count(_src))
  {
    std::cerr << "Source neuron '" << _src << "' is unknown." << std::endl;
    throw std::runtime_error("Robot brain error");
  }

  if (not layerMap_.count(_dst))
  {
    std::cerr << "Destination neuron '" << _dst << "' is unknown." << std::endl;
    throw std::runtime_error("Robot brain error");
  }

  auto srcLayer = layerMap_[_src];
  auto dstLayer = layerMap_[_dst];

  unsigned int srcNeuronPos = positionMap_[_src],
      dstNeuronPos = positionMap_[_dst];

  if ("input" == dstLayer)
  {
    std::cerr
        << "Destination neuron '"
        << _dst
        << "' is an input neuron."
        << std::endl;
    throw std::runtime_error("Robot brain error");
  }
  else if ("hidden" == dstLayer)
  {
    // Offset with output neurons for hidden neuron position
    dstNeuronPos += nOutputs_;
  }

  // Determine the index of the weight.
  unsigned int idx = (srcNeuronPos * MAX_NON_INPUT_NEURONS) + dstNeuronPos;
  if ("input" == srcLayer)
  {
    inputWeights_[idx] = _weight;
  }
  else if ("output" == srcLayer)
  {
    outputWeights_[idx] = _weight;
  }
  else
  {
    hiddenWeights_[idx] = _weight;
  }
}

/////////////////////////////////////////////////
void neuronHelper(
    double *params,
    unsigned int *types,
    sdf::ElementPtr neuron)
{
  if (not neuron->HasAttribute("type"))
  {
    std::cerr << "Missing required `type` attribute for neuron." << std::endl;
    throw std::runtime_error("Robot brain error");
  }

  const auto type = neuron->GetAttribute("type")->GetAsString();
  if ("Sigmoid" == type or "Simple" == type)
  {
    types[0] = ("Simple" == type ? SIMPLE : SIGMOID);

    if (not neuron->HasElement("rv:bias") or not neuron->HasElement("rv:gain"))
    {
      std::cerr
          << "A `"
          << type
          << "` neuron requires `rv:bias` and `rv:gain` elements."
          << std::endl;
      throw std::runtime_error("Robot brain error");
    }

    // Set bias and gain parameters
    params[0] = neuron->GetElement("rv:bias")->Get< double >();
    params[1] = neuron->GetElement("rv:gain")->Get< double >();
  }
  else if ("Oscillator" == type)
  {
    types[0] = OSCILLATOR;

    if (not neuron->HasElement("rv:period") or not neuron
        ->HasElement("rv:phase_offset") or not neuron
        ->HasElement("rv:amplitude"))
    {
      std::cerr << "An `Oscillator` neuron requires `rv:period`, "
          "`rv:phase_offset` and `rv:amplitude` elements." << std::endl;
      throw std::runtime_error("Robot brain error");
    }

    // Set period, phase offset and gain
    params[0] = neuron->GetElement("rv:period")->Get< double >();
    params[1] = neuron->GetElement("rv:phase_offset")->Get< double >();
    params[2] = neuron->GetElement("rv:amplitude")->Get< double >();
  }
  else
  {
    std::cerr << "Unsupported neuron type `" << type << '`' << std::endl;
    throw std::runtime_error("Robot brain error");
  }
}

/////////////////////////////////////////////////
void neuronHelper(
    double *params,
    unsigned int *types,
    const revolve::msgs::Neuron &neuron)
{
  const auto type = neuron.type();
  if ("Sigmoid" == type or "Simple" == type)
  {
    types[0] = "Simple" == type ? SIMPLE : SIGMOID;
    if (neuron.param_size() not_eq 2)
    {
      std::cerr << "A `" << type
                << "` neuron requires exactly two parameters." << std::endl;
      throw std::runtime_error("Robot brain error");
    }

    // Set bias and gain parameters
    params[0] = neuron.param(0).value();
    params[1] = neuron.param(1).value();
  }
  else if ("Oscillator" == type)
  {
    types[0] = OSCILLATOR;

    if (neuron.param_size() not_eq 3)
    {
      std::cerr << "A `" << type
                << "` neuron requires exactly three parameters." << std::endl;
      throw std::runtime_error("Robot brain error");
    }

    params[0] = neuron.param(0).value();
    params[1] = neuron.param(1).value();
    params[2] = neuron.param(2).value();
  }
  else
  {
    std::cerr << "Unsupported neuron type `" << type << '`' << std::endl;
    throw std::runtime_error("Robot brain error");
  }
}
