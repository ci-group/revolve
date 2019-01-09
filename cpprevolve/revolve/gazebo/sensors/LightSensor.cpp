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
* Author: Elte Hupkes
* Date: Mar 26, 2015
*
*/

#include <string>

#include <revolve/gazebo/sensors/LightSensor.h>

namespace gz = gazebo;

using namespace revolve::gazebo;

/////////////////////////////////////////////////
LightSensor::LightSensor(
    ::gazebo::physics::ModelPtr _model,
    sdf::ElementPtr _sensor,
    std::string _partId,
    std::string _sensorId)
    : Sensor(_model, _sensor, _partId, _sensorId, 1)
    , lastValue_(1.0)
{
  this->castSensor_ = std::dynamic_pointer_cast< gz::sensors::CameraSensor >(
      this->sensor_);

  if (not this->castSensor_)
  {
    std::cerr << "Creating a light sensor with a non-camera sensor object."
              << std::endl;
    throw std::runtime_error("Sensor error");
  }

  // Sensor must always update
  this->castSensor_->SetActive(true);

  // One byte per channel per pixel
  this->dataSize_ = 3 *
                    this->castSensor_->ImageWidth() *
                    this->castSensor_->ImageHeight();

  // Add update connection that will produce new value
  this->updateConnection_ = this->sensor_->ConnectUpdated(
      std::bind(&LightSensor::OnUpdate, this));
}

/////////////////////////////////////////////////
LightSensor::~LightSensor() = default;

/////////////////////////////////////////////////
void LightSensor::OnUpdate()
{
  // Average all channels and pixels to get a linear
  // light intensity.
  auto data = this->castSensor_->ImageData();
  auto avg = 0.0;
  for (size_t i = 0; i < this->dataSize_; ++i)
  {
    avg += (unsigned int)data[i];
  }

  avg /= this->dataSize_ * 255.f;

  this->lastValue_ = avg;
}

/////////////////////////////////////////////////
/// TODO Measure the fastest / most accurate way to use the light sensor.
///
/// Currently, we let Gazebo handle the light sensor update, because I assume
/// there may be some threading advantages there. However, this means that
/// the measurement of the sensor generally lags behind that of the IMU
/// sensor by as much as the actuation time (it might actually be more under
/// bad performance circumstances); which may or may not be an issue. The
/// alternative is to force the sensor to update while we are here in the
/// read method - although I have to check whether this is even possible. In
/// any case that would force the sensor update here on the "driver" thread,
/// which might be detrimental to performance.
void LightSensor::Read(double *_input)
{
  _input[0] = this->lastValue_;
}
