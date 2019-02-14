/*
 * Copyright (C) 2015-2018 Vrije Universiteit Amsterdam
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
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
 * Author: Milan Jelisavcic
 * Date: December 23, 2018
 *
 */

#include <revolve/gazebo/brains/BrainFactory.h>
#include <revolve/gazebo/brains/Brains.h>

namespace gz = gazebo;

using namespace revolve::gazebo;

/////////////////////////////////////////////////
BrainFactory::BrainFactory(::gazebo::physics::ModelPtr _model)
    : model_(_model)
{
}

/////////////////////////////////////////////////
BrainFactory::~BrainFactory() = default;

///////////////////////////////////////////////////
//BrainPtr BrainFactory::Brain(
//    sdf::ElementPtr _brainSdf,
//    const std::vector< MotorPtr > &_motors,
//    const std::vector< SensorPtr > &_sensors)
//{
//  BrainPtr brain = nullptr;
////  if ("ann" == _type)
////  {
////    brain.reset(new NeuralNetwork(model_, _brainSdf, _motors, _sensors));
////  }
////  else if ("rlpower" == _type)
////  {
////    brain.reset(new RLPower(model_, _brainSdf, _motors, _sensors));
////  }
////  else if ("diff_cpg" == type)
////  {
////    brain.reset(new );
////  }
//
//  return brain;
//}
//
///////////////////////////////////////////////////
//BrainPtr BrainFactory::Create(
//    sdf::ElementPtr _brainSdf,
//    const std::vector< MotorPtr > &_motors,
//    const std::vector< SensorPtr > &_sensors)
//{
////  auto typeParam = _motorSdf->GetAttribute("type");
////  auto partIdParam = _motorSdf->GetAttribute("part_id");
////  auto idParam = _motorSdf->GetAttribute("id");
////
////  if (not typeParam or not partIdParam or not idParam)
////  {
////    std::cerr << "Motor is missing required attributes (`id`, `type` or "
////                 "`part_id`)." << std::endl;
////    throw std::runtime_error("Motor error");
////  }
////
////  auto partId = partIdParam->GetAsString();
////  auto type = typeParam->GetAsString();
////  auto id = idParam->GetAsString();
//
//  BrainPtr brain = nullptr;
////      this->Brain(_brainSdf, _motors, _sensors);
////  assert(not brain || "[BrainFactory::Create] Brain type is unknown.");
//
//  return brain;
//}
