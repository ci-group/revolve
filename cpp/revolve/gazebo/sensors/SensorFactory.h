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
* Date: Mar 24, 2015
*
*/

#ifndef REVOLVE_GAZEBO_SENSORS_SENSORFACTORY_H_
#define REVOLVE_GAZEBO_SENSORS_SENSORFACTORY_H_

#include <revolve/gazebo/Types.h>
#include <gazebo/common/common.hh>

namespace revolve {
namespace gazebo {

class SensorFactory {
public:
  SensorFactory(::gazebo::physics::ModelPtr model);
  virtual ~SensorFactory();

  /**
   * Returns a sensor pointer instance from a motor element, part ID and type.
   * This is the convenience wrapper over `create` that has required attributes
   * already checked, usually you should override this when adding new sensor types.
   */
  virtual SensorPtr getSensor(sdf::ElementPtr sensor, const std::string & type,
                const std::string & partId, const std::string & sensorId);

  /**
   * Creates a new sensor in the given model, from the
   * given SDF element pointer.
   */
  virtual SensorPtr create(sdf::ElementPtr sensor);
protected:
  /**
   * Robot model for which this factory is generating sensors.
   */
  ::gazebo::physics::ModelPtr model_;
};

} /* namespace gazebo */
} /* namespace revolve */

#endif /* REVOLVE_GAZEBO_SENSORS_SENSORFACTORY_H_ */
