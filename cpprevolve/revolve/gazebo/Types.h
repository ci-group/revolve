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
*
*/

#ifndef REVOLVE_GZ_MODEL_TYPES_H_
#define REVOLVE_GZ_MODEL_TYPES_H_

#include <vector>

namespace revolve
{
  namespace gazebo
  {
    class Motor;

    class VirtualSensor;

    class Brain;

    class MotorFactory;

    class SensorFactory;

    class Evaluator;

    typedef std::shared_ptr< Brain > BrainPtr;

    typedef std::shared_ptr< Motor > MotorPtr;

    typedef std::shared_ptr< VirtualSensor > SensorPtr;

    typedef std::shared_ptr< MotorFactory > MotorFactoryPtr;

    typedef std::shared_ptr< SensorFactory > SensorFactoryPtr;

    typedef std::shared_ptr< Evaluator > EvaluatorPtr;

    typedef std::vector< double > Spline;

    typedef std::vector< Spline > Policy;

    typedef std::shared_ptr< Policy > PolicyPtr;
  }
}

#endif
