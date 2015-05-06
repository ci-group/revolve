/*
 * NeuralNetwork.cpp
 *
 *  Created on: Mar 16, 2015
 *      Author: elte
 */

#include <revolve/gazebo/brain/Brain.h>
#include <revolve/gazebo/motors/Motor.h>
#include <revolve/gazebo/sensors/Sensor.h>

#include <iostream>
#include <algorithm>
#include <stdexcept>
#include <cstdlib>
#include <map>
#include <string>
#include <sstream>

namespace revolve {
namespace gazebo {

// Internal helper function to build neuron params
void neuronHelper(float* params, unsigned int* types, sdf::ElementPtr neuron);

Brain::Brain(sdf::ElementPtr node, std::vector< MotorPtr > & motors, std::vector< SensorPtr > & sensors) {
	// We now setup the neural network and its parameters. The end result
	// of this operation should be that we can iterate/update all sensors in
	// a straightforward manner, likewise for the motors. We therefore first
	// create a map of all neurons, telling us how many there are for each
	// type, and what their properties are. We then iterate all sensors and
	// motors, creating the adequate neurons in place as we do so.

	// Connection weights; we can have connections from
	// every input / output / hidden neuron to every
	// output / hidden neuron. We fill weight with zeros immediately
	float weights[(MAX_INPUT_NEURONS + MAX_OUTPUT_NEURONS + MAX_HIDDEN_NEURONS)
	             * (MAX_OUTPUT_NEURONS + MAX_HIDDEN_NEURONS)];
	memset(weights, 0, sizeof(weights));

	// Neuron parameters, this is a maximum of 3 per neuron depending
	// on the type. Input neurons can have no params currently.
	float params[MAX_PARAMS * (MAX_OUTPUT_NEURONS + MAX_HIDDEN_NEURONS)];

	// Neuron types, input neurons are fixed
	unsigned int types[(MAX_OUTPUT_NEURONS + MAX_HIDDEN_NEURONS)];

	// Neuron counters
	unsigned int nInputs = 0, nOutputs = 0, nHidden = 0;

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
			if (nInputs >= MAX_INPUT_NEURONS) {
				std::cerr << "The number of input neurons(" << (nInputs + 1)
						<< ") is greater than the maximum allowed one ("
						<< MAX_INPUT_NEURONS << ")" << std::endl;
				throw std::runtime_error("Robot brain error");
			}

			toProcess.insert(neuronId);
			nInputs++;
		} else if ("output" == layer) {
			if (nOutputs >= MAX_OUTPUT_NEURONS) {
				std::cerr << "The number of output neurons(" << (nOutputs + 1)
						<< ") is greater than the maximum allowed one ("
						<< MAX_OUTPUT_NEURONS << ")" << std::endl;
				throw std::runtime_error("Robot brain error");
			}

			toProcess.insert(neuronId);
			nOutputs++;
		} else if ("hidden" == layer) {
			if (hiddenNeurons.size() >= MAX_HIDDEN_NEURONS) {
				std::cerr << "The number of hidden neurons(" << (hiddenNeurons.size() + 1)
						<< ") is greater than the maximum allowed one ("
						<< MAX_HIDDEN_NEURONS << ")" << std::endl;
				throw std::runtime_error("Robot brain error");
			}

			hiddenNeurons.push_back(neuronId);
			nHidden++;
		} else {
			std::cerr << "Unknown neuron layer '" << layer << "'." << std::endl;
			throw std::runtime_error("Robot brain error");
		}

		neuron = neuron->GetNextElement("rv:neuron");
	}

	// Create motor output neurons at the correct position
	unsigned int outPos = 0;
	for (auto it = motors.begin(); it != motors.end(); ++it) {
		auto motor = *it;
		for (unsigned int i = 0, l = motor->outputNeurons(); i < l; ++i) {
			std::stringstream neuronId;
			neuronId << motor->partId() << "-out-" << i;

			auto details = neuronMap.find(neuronId.str());
			if (details == neuronMap.end()) {
				std::cerr << "Required output neuron " << neuronId <<
						" for motor could not be located"
						<< std::endl;
				throw std::runtime_error("Robot brain error");
			}

			neuronHelper(&params[outPos * MAX_PARAMS], &types[outPos], neuron);
			positionMap[neuronId.str()] = outPos;
			toProcess.erase(neuronId.str());
			outPos++;
		}
	}

	// Create sensor input neurons
	unsigned int inPos = 0;
	for (auto it = sensors.begin(); it != sensors.end(); ++it) {
		auto sensor = *it;
		for (unsigned int i = 0, l = sensor->inputNeurons(); i < l; ++i) {
			std::stringstream neuronId;
			neuronId << sensor->partId() << "-in-" << i;

			auto details = neuronMap.find(neuronId.str());
			if (details == neuronMap.end()) {
				std::cerr << "Required input neuron " << neuronId <<
						" for motor could not be located"
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

		std::cerr << "Create virtual motors / sensors for input / output"
				" neurons that you would like to control manually.";
		throw std::runtime_error("Robot brain error");
	}

	// Add hidden neurons
	for (auto it = hiddenNeurons.begin(); it != hiddenNeurons.end(); ++it) {
		auto neuronId = *it;
		positionMap[neuronId] = outPos;
		neuronHelper(&params[outPos * MAX_PARAMS], &types[outPos], neuronMap[neuronId]);
		outPos++;
	}

	// Decode connections
	unsigned int nNonInputs = nOutputs + nHidden;
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
			srcNeuronPos += nOutputs;
		}

		if ("input" == dstLayer) {
			std::cerr << "Destination neuron '" << dst << "' is an input neuron." << std::endl;
			throw std::runtime_error("Robot brain error");
		} else if ("hidden" == dstLayer) {
			// Offset by outputs if hidden neuron
			dstNeuronPos += nOutputs;
		}

		// Determine the index of the weight.
		// Each output / hidden neuron can be used as an output, input
		// neurons can only be used as an input. By default, we offset
		// the index by the position of the neuron, which is the
		// correct position for an input neuron:
		unsigned int idx = (srcNeuronPos * nNonInputs) + dstNeuronPos;

		if ("input" != srcLayer) {
			// The output neuron list starts after all input neuron
			// connections, so we need to offset it from all
			// nInputs * nNonInputs of such connections:
			idx += (nInputs * nNonInputs);
		}

		// Set the weight; `Get` has a return argument here
		connection->GetAttribute("weight")->Get(weights[idx]);

		// Load the next connection
		connection = connection->GetNextElement("rv:connection");
	}

	// Create the actual neural network
	neuralNetwork_.reset(new NeuralNetwork);

	::nn_initNetwork(neuralNetwork_.get(), nInputs, nOutputs, nHidden,
		&weights[0], &params[0], &types[0]);
}

Brain::~Brain() {}

// TODO Check for erroneous / missing parameters
void neuronHelper(float* params, unsigned int* types, sdf::ElementPtr neuron) {
	if (!neuron->HasAttribute("type")) {
		std::cout << "Missing required `type` attribute for neuron." << std::endl;
				throw std::runtime_error("Robot brain error");
	}
	auto type = neuron->GetAttribute("type")->GetAsString();
	if ("sigmoid" == type || "simple" == type) {
		types[0] = "simple" == type ? SIMPLE : SIGMOID;

		// Set bias and gain parameters
		params[0] = neuron->GetElement("rv:bias")->Get< float >();
		params[1] = neuron->GetElement("rv:gain")->Get< float >();
	} else if ("oscillator" == type) {
		types[0] = OSCILLATOR;

		// Set period, phase offset and gain
		params[0] = neuron->GetElement("rv:period")->Get< float >();
		params[1] = neuron->GetElement("rv:phase_offset")->Get< float >();
		params[2] = neuron->GetElement("rv:gain")->Get< float >();
	} else {
		std::cout << "Only sigmoid and oscillator neurons supported currently." << std::endl;
		throw std::runtime_error("Robot brain error");
	}
}

void Brain::update(const std::vector<MotorPtr>& motors,
		const std::vector<SensorPtr>& sensors,
		double t, unsigned int step) {

	// Read sensor data and feed the neural network
	unsigned int p = 0;
	for (auto it = sensors.begin(); it != sensors.end(); ++it) {
		auto sensor = *it;
		sensor->read(&networkInputs_[p]);
		p += sensor->inputNeurons();
		//std::cout << "Sensor " << i << ", " << networkInputs_[i] << std::endl;
	}

	::nn_feed(neuralNetwork_.get(), &networkInputs_[0]);

	// Progress the neural network
	::nn_step(neuralNetwork_.get(), t);

	// Fetch the new output values
	::nn_fetch(neuralNetwork_.get(), &networkOutputs_[0]);

	// Send new signals to the motors
	p = 0;
	for (auto it = motors.begin(); it != motors.end(); ++it) {
		auto motor = *it;
		motor->update(&networkOutputs_[p], step);
		p += motor->outputNeurons();
	}
}


} /* namespace gazebo */
} /* namespace revolve_robogen */
