//
// Created by matteo on 8/21/19.
//

#pragma once

#include "Learner.h"
#include "Evaluator.h"
#include <multineat/Genome.h>
#include <multineat/Population.h>

namespace revolve {

class HyperNEAT: public Learner
{
public:
    HyperNEAT(std::unique_ptr<Controller> controller, std::unique_ptr<Evaluator> evaluator, const NEAT::Parameters &params, int seed);
    virtual ~HyperNEAT() = default;

    Controller *controller() override
    { return _controller.get(); }

    void optimize(double time, double dt) override;

private:
    float end_controller_time;
    std::unique_ptr<Controller> _controller;

    const NEAT::Parameters params;
    std::unique_ptr<NEAT::Population> population;
    std::vector<NEAT::Species>::iterator current_specie_evaluating;
    std::vector<NEAT::Genome>::iterator current_genome_evaluating;
};

}
