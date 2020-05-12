//
// Created by andi on 11-10-19.
//

#include <revolve/brains/controller/actuators/Actuator.h>
#include "Brain.h"

#include "DifferentialCPPNCPG.h"
#include "DifferentialCPG.h"

using namespace revolve::gazebo;

bool string_replace(std::string& str, const std::string& from, const std::string& to)
{
    size_t start_pos = str.find(from);
    int substitutions = 0;
    while (start_pos != std::string::npos)
    {
        str.replace(start_pos, from.length(), to);
        substitutions++;
        start_pos = str.find(from);
    }
    return substitutions > 0;
}


DifferentialCPPNCPG::DifferentialCPPNCPG(const sdf::ElementPtr brain_sdf,
                                           const std::vector<MotorPtr> &motors)
        : DifferentialCPG(
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
		const sdf::ElementPtr genome_sdf = brain_sdf->GetElement("rv:controller")->GetElement("rv:genome");
		const std::string genome_type = genome_sdf->GetAttribute("type")->GetAsString();
        if (genome_type != "CPPN")
        {
            throw std::runtime_error("unexpected GENOME type");
        }
        std::string genome_string = genome_sdf->GetValue()->GetAsString();
        string_replace(genome_string, "inf", std::to_string(std::numeric_limits<double>::max()));
		NEAT::Genome genome = NEAT::Genome();
		genome.Deserialize(genome_string);

		return genome;
}
