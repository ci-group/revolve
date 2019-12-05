//
// Created by matteo on 8/21/19.
//

#include "HyperNEAT.h"

using namespace revolve;

HyperNEAT::HyperNEAT(std::unique_ptr<Controller> controller, std::unique_ptr<Evaluator> evaluator, const NEAT::Parameters &params, const int seed)
        : Learner(std::move(evaluator))
        , end_controller_time(-1)
        , _controller(std::move(controller))
        , params(params)
        , population(nullptr)
{
    NEAT::Genome start_genome(0, 3, 0, 1,
                              false,
                              NEAT::UNSIGNED_SIGMOID,
                              NEAT::UNSIGNED_SIGMOID,
                              0,
                              this->params,
                              0);

    population.reset(new NEAT::Population(
            start_genome,
            params,
            true,
            1.0,
            seed
            ));

    current_specie_evaluating = population->m_Species.begin();
    current_genome_evaluating = current_specie_evaluating->m_Individuals.begin();
}

void HyperNEAT::optimize(const double time, const double dt)
{
    if (end_controller_time < 0) {
        end_controller_time = time;
        return;
    }
    if (end_controller_time < time) return;

    current_genome_evaluating->SetFitness(evaluator->fitness());

    //TODO report fitness back to the python manager

    // load next genome
    //TODO check if you finished the budget of generations

    current_genome_evaluating++;

    // Finished a species
    if (current_genome_evaluating == current_specie_evaluating->m_Individuals.end())
    {
        current_specie_evaluating++;

        // Finished all species -> Generate new generation
        if (current_specie_evaluating == population->m_Species.end())
        {
            population->Epoch();
            current_specie_evaluating = population->m_Species.begin();
        }

        current_genome_evaluating = current_specie_evaluating->m_Individuals.begin();
    }

    // You have a valid genome
    //TODO load genome in controller

    evaluator->reset();
}
