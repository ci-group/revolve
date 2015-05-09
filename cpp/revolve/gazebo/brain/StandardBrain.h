/*
 * NeuralNetwork.h
 *
 *  Created on: Mar 16, 2015
 *      Author: elte
 */

#ifndef REVOLVE_GAZEBO_BRAIN_STANDARDBRAIN_H_
#define REVOLVE_GAZEBO_BRAIN_STANDARDBRAIN_H_

#include <revolve/gazebo/Types.h>
#include <revolve/gazebo/brain/Brain.h>

#include <boost/shared_ptr.hpp>

#include <gazebo/common/common.hh>

extern "C" {
	#include <revolve/gazebo/brain/NeuralNetwork.h>
}

namespace revolve {
namespace gazebo {

class StandardBrain : public Brain {
public:
	/**
	 * @param The brain node
	 * @param Reference to motor list, will be reordered
	 * @param Reference to the sensor list, will be reordered
	 */
	StandardBrain(sdf::ElementPtr node, std::vector< MotorPtr > & motors, std::vector< SensorPtr > & sensors);
	virtual ~StandardBrain();

	/**
	* @param Motor list
	* @param Sensor list
	*/
	virtual void update(const std::vector< MotorPtr > & motors, const std::vector< SensorPtr > & sensors,
			double t, unsigned int step);

	// Input / output arrays used for the neural network,
	// these are stored with the object so they do not need
	// to be reallocated every time.
	float networkInputs_[MAX_INPUT_NEURONS];
	float networkOutputs_[MAX_OUTPUT_NEURONS];

protected:
	/**
	 * The neural network that controls the brain
	 */
	boost::shared_ptr< NeuralNetwork > neuralNetwork_;
};

} /* namespace gazebo */
} /* namespace revolve */

#endif /* REVOLVE_GAZEBO_BRAIN_STANDARDBRAIN_H_ */
