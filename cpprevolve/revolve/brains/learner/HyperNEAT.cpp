//
// Created by matteo on 8/21/19.
//

#include "HyperNEAT.h"

using namespace revolve;

HyperNEAT::HyperNEAT(
            std::unique_ptr<Controller> controller,
            Evaluator *evaluator,
            EvaluationReporter *reporter,
            const NEAT::Parameters &params,
            const int seed,
            const double evaluation_time,
            unsigned int n_evaluations)
        : Learner(evaluator, reporter, evaluation_time, n_evaluations)
        , _controller(std::move(controller))
        , params(params)
        , population(nullptr)
{
    NEAT::Genome start_genome(0, 3, 0, 1, //TODO these are also parameters
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
}

void HyperNEAT::init_first_controller()
{
    current_specie_evaluating = population->m_Species.begin();
    current_genome_evaluating = current_specie_evaluating->m_Individuals.begin();

    //TODO load genome in controller
}

void HyperNEAT::init_next_controller()
{
    // load next genome
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

    //TODO load genome in controller
}

void HyperNEAT::finalize_current_controller(double fitness)
{
    current_genome_evaluating->SetFitness(fitness);
}

void HyperNEAT::load_best_controller()
{
    //TODO load best genome into controller
}
