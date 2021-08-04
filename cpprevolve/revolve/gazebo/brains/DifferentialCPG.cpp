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
 * Author: Milan Jelisavcic & Maarten van Hooft
 * Date: December 29, 2018
 *
 * Cleaned up by andi on 06-10-19.
 *
 */

#include "DifferentialCPG.h"

namespace gz = gazebo;
using namespace revolve::gazebo;

DifferentialCPG::DifferentialCPG(const sdf::ElementPtr brain_sdf,
                                 const std::vector<MotorPtr> &_motors,
                                 std::shared_ptr<::revolve::AngleToTargetDetector> angle_to_target_sensor)
    : revolve::DifferentialCPG(load_params_from_sdf(brain_sdf), _motors, std::move(angle_to_target_sensor))
{
}

DifferentialCPG::DifferentialCPG(const sdf::ElementPtr brain_sdf,
                                 const std::vector<MotorPtr> &_motors,
                                 const NEAT::Genome &genome,
                                 std::shared_ptr<::revolve::AngleToTargetDetector> angle_to_target_sensor)
    : revolve::DifferentialCPG(load_params_from_sdf(brain_sdf), _motors, genome, std::move(angle_to_target_sensor))
{
}

revolve::DifferentialCPG::ControllerParams DifferentialCPG::load_params_from_sdf(sdf::ElementPtr brain_sdf)
{
  // Get all params from the sdf
  // TODO: Add exception handling
  sdf::ElementPtr controller_sdf = brain_sdf->GetElement("rv:controller");
  if (controller_sdf == nullptr)
    throw std::runtime_error("Controller element not found when reading CPG parameters");

  revolve::DifferentialCPG::ControllerParams params;
  //    params.reset_neuron_random =
  (controller_sdf->GetAttribute("reset_neuron_random")->Get<bool>(params.reset_neuron_random));
  //    params.use_frame_of_reference =
  (controller_sdf->GetAttribute("use_frame_of_reference")->Get<bool>(params.use_frame_of_reference));
  std::clog << "USE_FRAME_OF_REFERENCE: " << controller_sdf->GetAttribute("use_frame_of_reference")->GetAsString() << std::endl;
  params.init_neuron_state = stod(controller_sdf->GetAttribute("init_neuron_state")->GetAsString());
  params.range_ub = stod(controller_sdf->GetAttribute("range_ub")->GetAsString());
  params.output_signal_factor = stod(controller_sdf->GetAttribute("output_signal_factor")->GetAsString());
  params.abs_output_bound = stod(controller_sdf->GetAttribute("abs_output_bound")->GetAsString());

  // Get the weights from the sdf:
  // If loading with CPPN, the weights attribute does not exist
  if (controller_sdf->HasAttribute("weights"))
  {
    std::string sdf_weights = controller_sdf->GetAttribute("weights")->GetAsString();
    std::string delimiter = ";";

    size_t pos = 0;
    std::string token;
    while ((pos = sdf_weights.find(delimiter)) != std::string::npos)
    {
      token = sdf_weights.substr(0, pos);
      params.weights.push_back(stod(token));
      sdf_weights.erase(0, pos + delimiter.length());
    }
    // push the last element that does not end with the delimiter
    params.weights.push_back(stod(sdf_weights));
  }

  return params;
}
