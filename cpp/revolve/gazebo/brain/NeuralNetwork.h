/*
 * Brain class for the default Neural Network as specified by
 * Revolve. This is loosely based on the neural network
 * code provided with the Robogen framework.
 *
 * TODO Proper license attribution
 *
 * @author Elte Hupkes
 */

#ifndef REVOLVE_GAZEBO_BRAIN_NEURALNETWORK_H_
#define REVOLVE_GAZEBO_BRAIN_NEURALNETWORK_H_

#include "Brain.h"

// TODO This was true for Arduino, but we can change this
#define MAX_INPUT_NEURONS 13
#define MAX_OUTPUT_NEURONS 8

// Arbitrary value
#define MAX_HIDDEN_NEURONS 30

// (bias, tau, gain) or (phase offset, period, gain)
#define MAX_NEURON_PARAMS 3

namespace revolve {
namespace gazebo {

/*
 * Copied from NeuronRepresentation.h
 */
enum neuronType{
	INPUT,
	SIMPLE,
	SIGMOID,
	CTRNN_SIGMOID,
	OSCILLATOR,
	SUPG
};

class NeuralNetwork: public Brain {
public:
	/**
	 * @param The brain node
	 * @param Reference to motor list, which might be reordered
	 * @param Reference to the sensor list, which might be reordered
	 */
	NeuralNetwork(sdf::ElementPtr node, std::vector< MotorPtr > & motors, std::vector< SensorPtr > & sensors);
	virtual ~NeuralNetwork();

   /**
	* @param Motor list
	* @param Sensor list
	*/
	virtual void update(const std::vector< MotorPtr > & motors, const std::vector< SensorPtr > & sensors,
			double t, double step);

protected:
	/**
	 * Steps the neural network
	 */
	void step(double time);

	/*
	 * Connection weights.
	 *
	 * Given m input neurons and n output neurons
	 * m <= MAX_INPUT_NEURONS
	 * n <= MAX_OUTPUT_NEURONS
	 *
	 * One weight for each input-output connection (w_ij, input neuron i, 0 <= i <= m, output neuron j, 0 <= j <= n
	 * One weight for each output-output connection (wr_ij, output neuron i,j, 0 <= i,j <= n )
	 *
	 * The weights are saved as the concatenation by row of the following:
	 * w_00 w_01 ... w_0n
	 * w_10 w_11 ... w_1n
	 * ...  ...  ... ...
	 * w_m0 w_m1 ... w_mn
	 *
	 * wo_00 wo_01 ... wo_0n
	 * wo_10 wo_11 ... wo_1n
	 * ...  ...  ... ....
	 * wo_n0 wo_n1 ... wo_nn
	 */
	double weights_[(MAX_INPUT_NEURONS + MAX_OUTPUT_NEURONS + MAX_HIDDEN_NEURONS)
		             * (MAX_OUTPUT_NEURONS + MAX_HIDDEN_NEURONS)];

	/**
	 * Type of each non-input neuron
	 */
	unsigned int types_[(MAX_OUTPUT_NEURONS + MAX_HIDDEN_NEURONS)];

	/*
	 * Params for hidden and output neurons, quantity depends on the type of
	 * neuron
	 */
	double params_[MAX_NEURON_PARAMS * (MAX_OUTPUT_NEURONS + MAX_HIDDEN_NEURONS)];

	/**
	 * One input state for each input neuron
	 */
	double input_[MAX_INPUT_NEURONS];

	/*
	 * Output states arrays for the current state and the next state.
	 */
	double state1_[MAX_OUTPUT_NEURONS + MAX_HIDDEN_NEURONS];
	double state2_[MAX_OUTPUT_NEURONS + MAX_HIDDEN_NEURONS];

	/**
	 * Used to determine the current state array. False = state1,
	 * true = state2.
	 */
	bool flipState_;

	/**
	 * The number of inputs
	 */
	unsigned int nInputs_;

	/**
	 * The number of outputs
	 */
	unsigned int nOutputs_;

	/**
	 * The number of hidden units
	 */
	unsigned int nHidden_;

	/**
	 * The number of non-inputs (i.e. nOutputs + nHidden)
	 */
	unsigned int nNonInputs_;
};

} /* namespace gazebo */
} /* namespace revolve */

#endif /* REVOLVE_GAZEBO_BRAIN_NEURALNETWORK_H_ */
