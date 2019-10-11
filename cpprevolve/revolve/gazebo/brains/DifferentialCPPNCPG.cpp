//
// Created by andi on 11-10-19.
//

#include <revolve/brains/controller/actuators/Actuator.h>
#include "Brain.h"

#include "DifferentialCPPNCPG.h"

using namespace revolve::gazebo;

DifferentialCPGClean::DifferentialCPPNCPG(const sdf::ElementPtr brain_sdf,
                                           const std::vector<MotorPtr> &_motors)
        : Brain(), revolve::DifferentialCPG(load_params_from_sdf(brain_sdf),
                                            _motors,
                                            load_cppn_genome_from_sdf(brain_sdf)) {}


NEAT::Genome DifferentialCPPNCPG::load_cppn_genome_from_sdf(const sdf::ElementPtr brain_sdf) {
    // TODO
    NEAT::Genome gen;
    return gen;
}