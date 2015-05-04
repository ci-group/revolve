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

namespace revolve {
namespace gazebo {

// Internal helper function to build neuron params
void neuronHelper(float* params, unsigned int* types, unsigned int paramIdx,
		unsigned int typeIdx, const std::string& type, sdf::ElementPtr neuron);

Brain::Brain(sdf::ElementPtr node, std::vector< MotorPtr > & motors, std::vector< SensorPtr > & sensors) {
	// The neural network is initialized with
	// the following parameters (which are to be determined):
	// Number of inputs
	unsigned int nInputs = 0;

	// Number of outputs
	unsigned int nOutputs = 0;

	// Number of hidden neurons
	unsigned int nHidden = 0;

	// Connection weights; we can have connections from
	// every input / output / hidden neuron to every
	// output / hidden neuron. We fill weight with zeros immediately
	float weights[(MAX_INPUT_NEURONS + MAX_OUTPUT_NEURONS + MAX_HIDDEN_NEURONS)
	             * (MAX_OUTPUT_NEURONS + MAX_HIDDEN_NEURONS)];
	memset(weights, 0, sizeof(weights));

	// Neuron parameters, this is a maximum of 3
	// per neuron depending on the type.
	float params[MAX_PARAMS * (MAX_OUTPUT_NEURONS + MAX_HIDDEN_NEURONS)];

	// Neuron types, input neurons are fixed
	unsigned int types[(MAX_OUTPUT_NEURONS + MAX_HIDDEN_NEURONS)];

	// We now setup the neural network and its parameters. The end result
	// of this operation should be that we can iterate/update all sensors in
	// a straightforward manner, likewise for the motors. We therefore first
	// create a map of all neurons, telling us how many there are for each
	// type, and what their properties are. We then iterate all sensors and
	// motors, creating neurons as we do so.

	// TODO Implement all this
}

Brain::~Brain() {}

// TODO Check for erroneous / missing parameters
void neuronHelper(float* params, unsigned int* types, unsigned int paramIdx,
		unsigned int typeIdx, const std::string& type, sdf::ElementPtr neuron) {
	if ("sigmoid" == type) {
		types[typeIdx] = SIGMOID;

		// Set bias and gain parameters
		params[paramIdx] = neuron->GetElement("rv:bias")->Get< float >();
		params[paramIdx + 1] = neuron->GetElement("rv:gain")->Get< float >();
	} else if ("oscillator" == type) {
		types[typeIdx] = OSCILLATOR;

		// Set period, phase offset and gain
		params[paramIdx] = neuron->GetElement("rv:period")->Get< float >();
		params[paramIdx + 1] = neuron->GetElement("rv:phase_offset")->Get< float >();
		params[paramIdx + 2] = neuron->GetElement("rv:gain")->Get< float >();
	} else {
		std::cout << "only sigmoid and oscillator neurons supported currently" << std::endl;
		throw std::runtime_error("Robot brain error");
	}
}

void Brain::update(const std::vector<MotorPtr>& motors,
		const std::vector<SensorPtr>& sensors,
		double t, unsigned int step) {

	// Read sensor data and feed the neural network

	for (unsigned int i = 0, l = sensors.size(), p = 0; i < l; ++i) {
		sensors[i]->read(&networkInputs_[p]);
		p += sensors[i]->inputNeurons();
		//std::cout << "Sensor " << i << ", " << networkInputs_[i] << std::endl;
	}
	::nn_feed(neuralNetwork_.get(), &networkInputs_[0]);

	// Progress the neural network
	::nn_step(neuralNetwork_.get(), t);

	// Fetch the new output values
	::nn_fetch(neuralNetwork_.get(), &networkOutputs_[0]);

	// Send new signals to the motors
	for (unsigned int i = 0, l = motors.size(), p = 0; i < l; ++i) {
		motors[i]->update(&networkOutputs_[p], step);
		p += motors[i]->outputNeurons();
	}
}


} /* namespace gazebo */
} /* namespace revolve_robogen */
