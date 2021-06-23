//
// Created by andi on 06-10-19.
//

#include "DifferentialCPGClean.h"

using namespace revolve::gazebo;

DifferentialCPGClean::DifferentialCPGClean(const sdf::ElementPtr brain_sdf,
                                           const std::vector<MotorPtr> &_motors,
                                           std::shared_ptr<revolve::AngleToTargetDetector> angle_to_target_sensor)
        : revolve::DifferentialCPG(load_params_from_sdf(brain_sdf), _motors, angle_to_target_sensor)
{}

DifferentialCPGClean::DifferentialCPGClean(const sdf::ElementPtr brain_sdf,
				 const std::vector<MotorPtr> &_motors,
			 	 const NEAT::Genome &genome,
			 	 std::shared_ptr<revolve::AngleToTargetDetector> angle_to_target_sensor)
				: revolve::DifferentialCPG(load_params_from_sdf(brain_sdf), _motors, genome, angle_to_target_sensor)
{}

revolve::DifferentialCPG::ControllerParams DifferentialCPGClean::load_params_from_sdf(sdf::ElementPtr brain_sdf) {
    // Get all params from the sdf
    // TODO: Add exception handling
    sdf::ElementPtr controller_sdf = brain_sdf->GetElement("rv:controller");
    std::clog << "USE_FRAME_OF_REFERENCE: " << controller_sdf->GetAttribute("use_frame_of_reference")->GetAsString() << std::endl;
    revolve::DifferentialCPG::ControllerParams params;
    // params.reset_neuron_random =
            (controller_sdf->GetAttribute("reset_neuron_random")->Get<bool>(params.reset_neuron_random));
    // params.use_frame_of_reference =
            (controller_sdf->GetAttribute("use_frame_of_reference")->Get<bool>(params.use_frame_of_reference));
            params.use_frame_of_reference = true;
    params.init_neuron_state = stod(controller_sdf->GetAttribute("init_neuron_state")->GetAsString());
    params.range_ub = stod(controller_sdf->GetAttribute("range_ub")->GetAsString());
    params.output_signal_factor = stod(controller_sdf->GetAttribute("output_signal_factor")->GetAsString());
    params.abs_output_bound = stod(controller_sdf->GetAttribute("abs_output_bound")->GetAsString());

    // Get the weights from the sdf:
    // If loading with CPPN, the weights attribute does not exist
    if (controller_sdf->HasAttribute("weights")) {
				std::string sdf_weights = controller_sdf->GetAttribute("weights")->GetAsString();
				std::string delimiter = ";";

				size_t pos = 0;
				std::string token;
				while ((pos = sdf_weights.find(delimiter)) != std::string::npos) {
						token = sdf_weights.substr(0, pos);
						params.weights.push_back(stod(token));
						sdf_weights.erase(0, pos + delimiter.length());
				}
				// push the last element that does not end with the delimiter
				params.weights.push_back(stod(sdf_weights));
		}

    return params;
}
