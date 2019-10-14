//
// Created by andi on 11-10-19.
//

#include <revolve/brains/controller/actuators/Actuator.h>
#include "Brain.h"

#include "DifferentialCPPNCPG.h"
#include "DifferentialCPGClean.h"

using namespace revolve::gazebo;

DifferentialCPPNCPG::DifferentialCPPNCPG(const sdf::ElementPtr brain_sdf,
                                           const std::vector<MotorPtr> &motors)
        : DifferentialCPGClean(
        				brain_sdf,
        				motors,
								DifferentialCPPNCPG::load_cppn_genome_from_sdf(brain_sdf))
{}

/// \brief extracts CPPN genome from brain_sdf
/// \param[in] brain_sdf ElementPtr containing the "brain" - tag of the model sdf
/// \return the NEAT genome
/// \details Loads genome from SDF as string and deserializes it into type type NEAT::Genome
NEAT::Genome DifferentialCPPNCPG::load_cppn_genome_from_sdf(const sdf::ElementPtr brain_sdf)
{
		sdf::ElementPtr genome_sdf = brain_sdf->GetElement("rv:controller")->GetElement("rv:genome");
		std::string genome_string = genome_sdf->GetAttribute("serial_genome")->GetAsString();
		NEAT::Genome genome = NEAT::Genome();
		genome.Deserialize(genome_string);

		return genome;
}
