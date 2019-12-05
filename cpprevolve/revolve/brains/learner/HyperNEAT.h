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
    explicit HyperNEAT(
            std::unique_ptr<Controller> controller,
            Evaluator *evaluator,
            EvaluationReporter *reporter,
            const NEAT::Parameters &params,
            int seed,
            double evaluation_time,
            unsigned int n_evaluations);

    virtual ~HyperNEAT() = default;

    Controller *controller() override
    { return _controller.get(); }

    void optimize(double time, double dt) override;

private:
    double evaluation_time;
    double end_controller_time;
    std::unique_ptr<Controller> _controller;

    const NEAT::Parameters params;
    std::unique_ptr<NEAT::Population> population;
    unsigned int evaluation_counter;
    unsigned int n_evaluations;
    std::vector<NEAT::Species>::iterator current_specie_evaluating;
    std::vector<NEAT::Genome>::iterator current_genome_evaluating;
};

}
