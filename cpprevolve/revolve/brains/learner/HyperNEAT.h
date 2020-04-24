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

    ~HyperNEAT() override = default;

    Controller *controller() override
    { return _controller.get(); }

    void init_first_controller() override;
    void init_next_controller() override;
    void finalize_current_controller(double fitness) override;
    void load_best_controller() override;

private:
    std::unique_ptr<Controller> _controller;

    const NEAT::Parameters params;
    std::unique_ptr<NEAT::Population> population;
    std::vector<NEAT::Species>::iterator current_specie_evaluating;
    std::vector<NEAT::Genome>::iterator current_genome_evaluating;
    double best_fitness = -std::numeric_limits<double>::infinity();
    std::vector<NEAT::Genome>::iterator best_genome;

protected:
    /// \brief function to load a genome into a controller
    std::function<void(std::vector<NEAT::Genome>::iterator)> load_genome;
};

}
