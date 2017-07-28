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
* Description: The `VirtualSensor` is the base class for all Sensors, it
*              defines the sensor interface but is not necessarily connected
*              to anything concrete in the simulation.
* Author: Elte Hupkes
*
*/

#ifndef REVOLVE_GAZEBO_SENSORS_VIRTUALSENSOR_H_
#define REVOLVE_GAZEBO_SENSORS_VIRTUALSENSOR_H_

#include <string>

#include <gazebo/gazebo.hh>
#include <gazebo/sensors/sensors.hh>

#include <revolve/gazebo/Types.h>

namespace revolve {
namespace gazebo {

class VirtualSensor {
  public:
  VirtualSensor(::gazebo::physics::ModelPtr model, std::string partId, std::string sensorId, unsigned int inputs);
  virtual ~VirtualSensor();

  /**
   * Reads the current value of this sensor into the given network
   * output array. This should fill the number of input neurons
   * the sensor specifies to have, i.e. if the sensor specifies 2
   * input neurons it should fill `input[0]` and `input[1]`
   */
  virtual void read(double * input) = 0;

  /**
   * @return The part ID
   */
  std::string partId();

  /**
   * @return The ID of the sensor
   */
  std::string sensorId();

  /**
   * @return Number of inputs this sensor generates
   */
  unsigned int inputs();

  protected:
  /**
   * The model this sensor is part of
   */
  ::gazebo::physics::ModelPtr model_;

  /**
   * ID of the body part the motor belongs to
   */
  std::string partId_;

  /**
   * ID of the sensor
   */
  std::string sensorId_;

  /**
   * Number of inputs this sensor generates
   */
  unsigned int inputs_;
};

} /* namespace gazebo */
} /* namespace revolve */

#endif /* REVOLVE_GAZEBO_SENSORS_VIRTUALSENSOR_H_ */
