/*
 * LightSensor.cpp
 *
 *  Created on: Mar 26, 2015
 *      Author: elte
 */

#include <revolve/gazebo/sensors/LightSensor.h>

#include <boost/bind.hpp>

namespace gz = gazebo;

namespace revolve {
namespace gazebo {

LightSensor::LightSensor(::gazebo::physics::ModelPtr model, sdf::ElementPtr sensor,
		std::string partId, std::string sensorId):
	Sensor(model, sensor, partId, sensorId, 1),

	// Initialize light sensor to full intensity
	lastValue_(1.0)
{
	this->castSensor_ = boost::dynamic_pointer_cast<gz::sensors::CameraSensor>(this->sensor_);

	if (!this->castSensor_) {
		std::cerr << "Creating a light sensor with a non-camera sensor object." << std::endl;
		throw std::runtime_error("Sensor error");
	}

	// Sensor must always update
	this->castSensor_->SetActive(true);

	// One byte per channel per pixel
	this->dataSize_ = 3 * this->castSensor_->GetImageWidth() * this->castSensor_->GetImageHeight();

	// Add update connection that will produce new value
	this->updateConnection_ = this->sensor_->ConnectUpdated(boost::bind(&LightSensor::OnUpdate, this));
}

LightSensor::~LightSensor()
{}

void LightSensor::OnUpdate() {
	// Average all channels and pixels to get a linear
	// light intensity.
	const unsigned char* data = this->castSensor_->GetImageData();
	float avg = 0;
	for (unsigned int i = 0; i < this->dataSize_; ++i) {
		avg += (unsigned int)data[i];
	}

	avg /= this->dataSize_ * 255.f;

	this->lastValue_ = avg;
}

/**
 * TODO Measure the fastest / most accurate way to use the light sensor.
 *
 * Currently, we let Gazebo handle the light sensor update, because
 * I assume there may be some threading advantages there. However,
 * this means that the measurement of the sensor generally lags
 * behind that of the IMU sensor by as much as the actuation time
 * (it might actually be more under bad performance circumstances);
 * which may or may not be an issue. The alternative is to force
 * the sensor to update while we are here in the read method -
 * although I have to check whether this is even possible. In any
 * case that would force the sensor update here on the "driver"
 * thread, which might be detrimental to performance.
 */
void LightSensor::read(double * input) {
	input[0] = lastValue_;
}

} /* namespace gazebo */
} /* namespace tol_robogen */
