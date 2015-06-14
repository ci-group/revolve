/*
 *
 */

#include <revolve/gazebo/brain/NeuralNetwork.h>
#include <revolve/gazebo/motors/Motor.h>
#include <revolve/gazebo/sensors/Sensor.h>

#include <iostream>
#include <algorithm>
#include <stdexcept>
#include <cstdlib>
#include <map>
#include <string>
#include <sstream>
#include <cmath>

namespace revolve {
namespace gazebo {

// Internal helper function to build neuron params
void neuronHelper(double* params, unsigned int* types, sdf::ElementPtr neuron);

NeuralNetwork::NeuralNetwork(sdf::ElementPtr node, std::vector< MotorPtr > & motors,
		std::vector< SensorPtr > & sensors):
	nInputs_(0),
	nOutputs_(0),
	nHidden_(0),
	nNonInputs_(0),
	flipState_(false)
{
	// Initialize weights, input and states to zero by default
	memset(weights_, 0, sizeof(weights_));
	memset(state1_, 0, sizeof(state1_));
	memset(state2_, 0, sizeof(state2_));
	memset(input_, 0, sizeof(input_));

	// We now setup the neural network and its parameters. The end result
	// of this operation should be that we can iterate/update all sensors in
	// a straightforward manner, likewise for the motors. We therefore first
	// create a map of all neurons, telling us how many there are for each
	// type, and what their properties are. We then iterate all sensors and
	// motors, creating the adequate neurons in place as we do so.

	// Map of ID to neuron element
	std::map<std::string, sdf::ElementPtr> neuronMap;

	// Stores the type of each neuron ID
	std::map<std::string, std::string> layerMap;

	// Stores the position of each neuron ID, relative to its type
	std::map<std::string, unsigned int> positionMap;

	// List of all hidden neurons for convenience
	std::vector<std::string> hiddenNeurons;

	// Set for tracking all collected input/output neurons
	std::set<std::string> toProcess;

	// Fetch the first neuron; note the HasElement call is necessary to prevent SDF from complaining
	// if no neurons are present.
	auto neuron = node->HasElement("rv:neuron") ? node->GetElement("rv:neuron") : sdf::ElementPtr();
	while (neuron) {
		if (!neuron->HasAttribute("layer") || !neuron->HasAttribute("id")) {
			std::cerr << "Missing required neuron attributes (id or layer). '" << std::endl;
			throw std::runtime_error("Robot brain error");
		}
		auto layer = neuron->GetAttribute("layer")->GetAsString();
		auto neuronId = neuron->GetAttribute("id")->GetAsString();

		if (layerMap.count(neuronId)) {
			std::cerr << "Duplicate neuron ID '"
					<< neuronId << "'" << std::endl;
			throw std::runtime_error("Robot brain error");
		}

		layerMap[neuronId] = layer;
		neuronMap[neuronId] = neuron;

		if ("input" == layer) {
			if (nInputs_ >= MAX_INPUT_NEURONS) {
				std::cerr << "The number of input neurons(" << (nInputs_ + 1)
						<< ") is greater than the maximum allowed one ("
						<< MAX_INPUT_NEURONS << ")" << std::endl;
				throw std::runtime_error("Robot brain error");
			}

			toProcess.insert(neuronId);
			nInputs_++;
		} else if ("output" == layer) {
			if (nOutputs_ >= MAX_OUTPUT_NEURONS) {
				std::cerr << "The number of output neurons(" << (nOutputs_ + 1)
						<< ") is greater than the maximum allowed one ("
						<< MAX_OUTPUT_NEURONS << ")" << std::endl;
				throw std::runtime_error("Robot brain error");
			}

			toProcess.insert(neuronId);
			nOutputs_++;
		} else if ("hidden" == layer) {
			if (hiddenNeurons.size() >= MAX_HIDDEN_NEURONS) {
				std::cerr << "The number of hidden neurons(" << (hiddenNeurons.size() + 1)
						<< ") is greater than the maximum allowed one ("
						<< MAX_HIDDEN_NEURONS << ")" << std::endl;
				throw std::runtime_error("Robot brain error");
			}

			hiddenNeurons.push_back(neuronId);
			nHidden_++;
		} else {
			std::cerr << "Unknown neuron layer '" << layer << "'." << std::endl;
			throw std::runtime_error("Robot brain error");
		}

		neuron = neuron->GetNextElement("rv:neuron");
	}

	// Create motor output neurons at the correct position
	// We iterate a part's motors and just assign every
	// neuron we find in order.
	std::map<std::string, unsigned int> outputCountMap;
	unsigned int outPos = 0;
	for (auto it = motors.begin(); it != motors.end(); ++it) {
		auto motor = *it;
		auto partId = motor->partId();
		if (!outputCountMap.count(partId)) {
			outputCountMap[partId] = 0;
		}

		for (unsigned int i = 0, l = motor->outputs(); i < l; ++i) {
			std::stringstream neuronId;
			neuronId << partId << "-out-" << outputCountMap[partId];
			outputCountMap[partId]++;

			auto details = neuronMap.find(neuronId.str());
			if (details == neuronMap.end()) {
				std::cerr << "Required output neuron " << neuronId.str() <<
						" for motor could not be located"
						<< std::endl;
				throw std::runtime_error("Robot brain error");
			}

			neuronHelper(&params_[outPos * MAX_NEURON_PARAMS], &types_[outPos], details->second);
			positionMap[neuronId.str()] = outPos;
			toProcess.erase(neuronId.str());
			outPos++;
		}
	}

	// Create sensor input neurons
	std::map<std::string, unsigned int> inputCountMap;
	unsigned int inPos = 0;
	for (auto it = sensors.begin(); it != sensors.end(); ++it) {
		auto sensor = *it;
		auto partId = sensor->partId();

		if (!inputCountMap.count(partId)) {
			inputCountMap[partId] = 0;
		}

		for (unsigned int i = 0, l = sensor->inputs(); i < l; ++i) {
			std::stringstream neuronId;
			neuronId << partId << "-in-" << inputCountMap[partId];
			inputCountMap[partId]++;

			auto details = neuronMap.find(neuronId.str());
			if (details == neuronMap.end()) {
				std::cerr << "Required input neuron " << neuronId.str() <<
						" for sensor could not be located"
						<< std::endl;
				throw std::runtime_error("Robot brain error");
			}

			// Input neurons can currently not have a type, so
			// there is no need to process it.
			positionMap[neuronId.str()] = inPos;
			toProcess.erase(neuronId.str());
			inPos++;
		}
	}

	// Check if there are any input / output neurons which have not
	// yet been processed. This is an error - every input / output
	// neuron should be connected to at least a virtual motor / sensor.
	if (toProcess.size()) {
		std::cerr << "The following input / output neurons were"
				" defined, but not attached to any sensor / motor:" << std::endl;

		for (auto it = toProcess.begin(); it != toProcess.end(); ++it) {
			std::cerr << (*it) << std::endl;
		}

		std::cerr << "Create virtual sensor and motors for input / output"
				" neurons that you would like to control manually.";
		throw std::runtime_error("Robot brain error");
	}

	// Add hidden neurons
	for (auto it = hiddenNeurons.begin(); it != hiddenNeurons.end(); ++it) {
		auto neuronId = *it;
		positionMap[neuronId] = outPos;
		neuronHelper(&params_[outPos * MAX_NEURON_PARAMS], &types_[outPos], neuronMap[neuronId]);
		outPos++;
	}

	// Decode connections
	nNonInputs_ = nOutputs_ + nHidden_;
	auto connection = node->HasElement("rv:connection") ? node->GetElement("rv:connection") : sdf::ElementPtr();
	while (connection) {
		if (!connection->HasAttribute("src") || !connection->HasAttribute("dst")
				|| !connection->HasAttribute("weight")) {
			std::cerr << "Missing required connection attributes (`src`, `dst` or `weight`)." << std::endl;
			throw std::runtime_error("Robot brain error");
		}

		auto src = connection->GetAttribute("src")->GetAsString();
		auto dst = connection->GetAttribute("dst")->GetAsString();

		if (!layerMap.count(src)) {
			std::cerr << "Source neuron '" << src << "' is unknown." << std::endl;
			throw std::runtime_error("Robot brain error");
		}

		if (!layerMap.count(dst)) {
			std::cerr << "Destination neuron '" << dst << "' is unknown." << std::endl;
			throw std::runtime_error("Robot brain error");
		}

		auto srcLayer = layerMap[src];
		auto dstLayer = layerMap[dst];

		int srcNeuronPos;
		int dstNeuronPos;

		srcNeuronPos = positionMap[src];
		dstNeuronPos = positionMap[dst];

		if ("hidden" == srcLayer) {
			// Offset by outputs if hidden neuron; nothing
			// needs to happen for output or input neurons.
			srcNeuronPos += nOutputs_;
		}

		if ("input" == dstLayer) {
			std::cerr << "Destination neuron '" << dst << "' is an input neuron." << std::endl;
			throw std::runtime_error("Robot brain error");
		} else if ("hidden" == dstLayer) {
			// Offset by outputs if hidden neuron
			dstNeuronPos += nOutputs_;
		}

		// Determine the index of the weight.
		// Each output / hidden neuron can be used as an output, input
		// neurons can only be used as an input. By default, we offset
		// the index by the position of the neuron, which is the
		// correct position for an input neuron:
		unsigned int idx = (srcNeuronPos * nNonInputs_) + dstNeuronPos;

		if ("input" != srcLayer) {
			// The output neuron list starts after all input neuron
			// connections, so we need to offset it from all
			// nInputs * nNonInputs of such connections:
			idx += (nInputs_ * nNonInputs_);
		}

		// Set the weight; `Get` has a return argument here
		connection->GetAttribute("weight")->Get(weights_[idx]);

		// Load the next connection
		connection = connection->GetNextElement("rv:connection");
	}
}

NeuralNetwork::~NeuralNetwork()
{}

void NeuralNetwork::step(double time) {
	unsigned int i = 0;
	unsigned int j = 0;

	if (nOutputs_ == 0) {
		return;
	}

	double *curState, *nextState;
	if (flipState_) {
		curState = state2_;
		nextState = state1_;
	} else {
		curState = state1_;
		nextState = state2_;
	}


	unsigned int baseIndexOutputWeights = nNonInputs_ * nInputs_;
	for (i = 0; i < nNonInputs_; ++i) {
		double curNeuronActivation = 0;

		for (j = 0; j < nInputs_; ++j) {
			curNeuronActivation += weights_[nNonInputs_ * j + i]
					* input_[j];
		}

		for (j = 0; j < nNonInputs_; ++j) {
			curNeuronActivation += weights_[baseIndexOutputWeights
					+ nNonInputs_ * j + i] * curState[j];
		}

		switch (types_[i]) {
		case SIGMOID:
			/* params are bias, gain */
			curNeuronActivation -= params_[MAX_NEURON_PARAMS*i];
			nextState[i] = 1.0
				/ (1.0 + exp(-params_[MAX_NEURON_PARAMS*i+1] *
						curNeuronActivation));
			break;
		case SIMPLE:
			/* linear, params are bias, gain */
			curNeuronActivation -= params_[MAX_NEURON_PARAMS*i];
			nextState[i] = params_[MAX_NEURON_PARAMS*i+1] *
					curNeuronActivation;
			break;
		case OSCILLATOR: { // Use the block to prevent "crosses initialization" error
			/* TODO should this consider inputs too?? */
			/* params are period, phase offset, gain (amplitude) */
			double period = params_[MAX_NEURON_PARAMS*i];
			double phaseOffset = params_[MAX_NEURON_PARAMS*i + 1];
			double gain = params_[MAX_NEURON_PARAMS*i + 2];
			nextState[i] = ((sin( (2.0*M_PI/period) *
				 (time - period * phaseOffset))) + 1.0) / 2.0;

			/* set output to be in [0.5 - gain/2, 0.5 + gain/2] */
			nextState[i] = (0.5 - (gain/2.0) +
					nextState[i] * gain);
		} break;
		default:
			// Unsupported type will have been caught in the
			// constructor.
			break;
		}
	}

	flipState_ = !flipState_;
}

void NeuralNetwork::update(const std::vector<MotorPtr>& motors,
		const std::vector<SensorPtr>& sensors,
		double t, unsigned int step) {

	// Read sensor data and feed the neural network
	unsigned int p = 0;
	for (auto it = sensors.begin(); it != sensors.end(); ++it) {
		auto sensor = *it;
		sensor->read(&input_[p]);
		p += sensor->inputs();
	}

	this->step(t);

	// Since the output neurons are the first in the state
	// array we can just use it to update the motors directly.
	double * output = flipState_ ? &state2_[0] : &state1_[0];

	// Send new signals to the motors
	p = 0;
	for (auto it = motors.begin(); it != motors.end(); ++it) {
		auto motor = *it;
		motor->update(&output[p], step);
		p += motor->outputs();
	}
}

// TODO Check for erroneous / missing parameters
void neuronHelper(double* params, unsigned int* types, sdf::ElementPtr neuron) {
	if (!neuron->HasAttribute("type")) {
		std::cerr << "Missing required `type` attribute for neuron." << std::endl;
				throw std::runtime_error("Robot brain error");
	}

	auto type = neuron->GetAttribute("type")->GetAsString();
	if ("Sigmoid" == type || "Simple" == type) {
		types[0] = "Simple" == type ? SIMPLE : SIGMOID;

		if (!neuron->HasElement("rv:bias") || !neuron->HasElement("rv:gain")) {
			std::cerr << "A `Simple` neuron requires `rv:bias` and `rv:gain` elements." << std::endl;
			throw std::runtime_error("Robot brain error");
		}

		// Set bias and gain parameters
		params[0] = neuron->GetElement("rv:bias")->Get< double >();
		params[1] = neuron->GetElement("rv:gain")->Get< double >();
	} else if ("Oscillator" == type) {
		types[0] = OSCILLATOR;

		if (!neuron->HasElement("rv:period") || !neuron->HasElement("rv:phase_offset") ||
				!neuron->HasElement("rv:amplitude")) {
			std::cerr << "An `Oscillator` neuron requires `rv:period`, `rv:phase_offset` and `rv:amplitude` elements." << std::endl;
			throw std::runtime_error("Robot brain error");
		}

		// Set period, phase offset and gain
		params[0] = neuron->GetElement("rv:period")->Get< double >();
		params[1] = neuron->GetElement("rv:phase_offset")->Get< double >();
		params[2] = neuron->GetElement("rv:amplitude")->Get< double >();
	} else {
		std::cerr << "Only `Sigmoid` and `Oscillator` neurons supported currently, "
				"given type is `" << type << '`' << std::endl;
		throw std::runtime_error("Robot brain error");
	}
}

} /* namespace gazebo */
} /* namespace revolve */
