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
#include <gazebo/gazebo.hh>
#include <revolve/msgs/neural_net.pb.h>

// These numbers are quite arbitrary. It used to be in:13 out:8
// for the Arduino, but I upped them both to 20 to accomodate other
// scenarios. Should really be enforced in the Python code, this
// implementation should not be the limit.
#define MAX_INPUT_NEURONS 20
#define MAX_OUTPUT_NEURONS 20

// Arbitrary value
#define MAX_HIDDEN_NEURONS 30

// Convenience
#define MAX_NON_INPUT_NEURONS (MAX_HIDDEN_NEURONS + MAX_OUTPUT_NEURONS)

// (bias, tau, gain) or (phase offset, period, gain)
#define MAX_NEURON_PARAMS 3

namespace revolve {
namespace gazebo {

typedef const boost::shared_ptr<revolve::msgs::ModifyNeuralNetwork const> ConstModifyNeuralNetworkPtr;

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
	 * @param Name of the robot
	 * @param The brain node
	 * @param Reference to motor list, which might be reordered
	 * @param Reference to the sensor list, which might be reordered
	 */
	NeuralNetwork(std::string modelName, sdf::ElementPtr node,
				  std::vector< MotorPtr > & motors, std::vector< SensorPtr > & sensors);
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

	/**
	 * Request handler to modify the neural network
	 */
	void modify(ConstModifyNeuralNetworkPtr &req);

	// Mutex for stepping / updating the network
	boost::mutex networkMutex_;

	/**
	 * Transport node
	 */
	::gazebo::transport::NodePtr node_;

	/**
	 * Network modification subscriber
	 */
	::gazebo::transport::SubscriberPtr alterSub_;

	/*
	 * Connection weights, separated into three arrays for convenience. Note
	 * that only output and hidden neurons are weight targets.
	 *
	 * Weights are stored with gaps, meaning that every neuron holds entries for
	 * the maximum possible number of connections. This makes restructuring the
	 * weights arrays when a hidden neuron is removed slightly less cumbersome.
	 */
	double inputWeights_[MAX_INPUT_NEURONS * (MAX_OUTPUT_NEURONS + MAX_HIDDEN_NEURONS)];
	double outputWeights_[MAX_OUTPUT_NEURONS * (MAX_OUTPUT_NEURONS + MAX_HIDDEN_NEURONS)];
	double hiddenWeights_[MAX_HIDDEN_NEURONS * (MAX_OUTPUT_NEURONS + MAX_HIDDEN_NEURONS)];

	// Unlike weights, types, params and current states are stored without
	// gaps, meaning the first `m` entries are for output neurons, followed
	// by `n` entries for hidden neurons. If a hidden neuron is removed,
	// the items beyond it are moved back.
	/**
	 * Type of each non-input neuron
	 */
	unsigned int types_[(MAX_OUTPUT_NEURONS + MAX_HIDDEN_NEURONS)];

	/*
	 * Params for hidden and output neurons, quantity depends on the type of
	 * neuron
	 */
	double params_[MAX_NEURON_PARAMS * (MAX_OUTPUT_NEURONS + MAX_HIDDEN_NEURONS)];

	/*
	 * Output states arrays for the current state and the next state.
	 */
	double state1_[MAX_OUTPUT_NEURONS + MAX_HIDDEN_NEURONS];
	double state2_[MAX_OUTPUT_NEURONS + MAX_HIDDEN_NEURONS];

	/**
	 * One input state for each input neuron
	 */
	double input_[MAX_INPUT_NEURONS];

	/**
	 * Used to determine the current state array. False = state1,
	 * true = state2.
	 */
	bool flipState_;

	/**
	 * Stores the type of each neuron ID
	 */
	std::map<std::string, std::string> layerMap_;

	/**
	 * Stores the position of each neuron ID, relative to its type
	 */
	std::map<std::string, unsigned int> positionMap_;

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
private:
	void connectionHelper(const std::string & src, const std::string & dst, double weight);
};

} /* namespace gazebo */
} /* namespace revolve */

#endif /* REVOLVE_GAZEBO_BRAIN_NEURALNETWORK_H_ */
