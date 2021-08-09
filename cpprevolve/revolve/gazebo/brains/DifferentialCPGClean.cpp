//
// Created by andi on 06-10-19.
//

#include "DifferentialCPGClean.h"

using namespace revolve::gazebo;

DifferentialCPGClean::DifferentialCPGClean(const sdf::ElementPtr brain_sdf,
                                           const std::vector<MotorPtr> &_motors)
        : Brain()
        , revolve::DifferentialCPG(load_params_from_sdf(brain_sdf), _motors)
{}

DifferentialCPGClean::DifferentialCPGClean(const sdf::ElementPtr brain_sdf,
				 const std::vector<MotorPtr> &_motors,
			 	 const NEAT::Genome &genome)
				: Brain()
				, revolve::DifferentialCPG(load_params_from_sdf(brain_sdf), _motors, genome)
{}


void DifferentialCPGClean::Update(const std::vector<MotorPtr> &_motors,
                                  const std::vector<SensorPtr> &_sensors,
                                  const double _time,
                                  const double _step)
{
    this->::revolve::DifferentialCPG::update(_motors, _sensors, _time, _step);
}

revolve::DifferentialCPG::ControllerParams DifferentialCPGClean::load_params_from_sdf(sdf::ElementPtr brain_sdf) {
    // Get all params from the sdf
    // TODO: Add exception handling
    sdf::ElementPtr controller_sdf = brain_sdf->GetElement("rv:controller");
    revolve::DifferentialCPG::ControllerParams params;
    params.reset_neuron_random = (controller_sdf->GetAttribute("reset_neuron_random")->GetAsString() == "true");
    params.use_frame_of_reference = (controller_sdf->GetAttribute("use_frame_of_reference")->GetAsString() == "true");
    params.init_neuron_state = stod(controller_sdf->GetAttribute("init_neuron_state")->GetAsString());
    params.range_ub = stod(controller_sdf->GetAttribute("range_ub")->GetAsString());
    params.signal_factor_all = stod(controller_sdf->GetAttribute("signal_factor_all")->GetAsString());
    params.signal_factor_mid = stod(controller_sdf->GetAttribute("signal_factor_mid")->GetAsString());
    params.signal_factor_left_right = stod(controller_sdf->GetAttribute("signal_factor_left_right")->GetAsString());
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
