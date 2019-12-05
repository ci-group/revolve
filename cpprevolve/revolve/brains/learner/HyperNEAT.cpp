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
        : Learner(evaluator, reporter)
        , evaluation_time(evaluation_time)
        , end_controller_time(-1)
        , _controller(std::move(controller))
        , params(params)
        , population(nullptr)
        , evaluation_counter(0)
        , n_evaluations(n_evaluations)
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

    evaluation_counter++;
    double fitness = evaluator->fitness();
    //TODO check if you finished the budget of generations
    bool finished = evaluation_counter >= n_evaluations;

    evaluation_reporter->report(evaluation_counter, finished, fitness);
    current_genome_evaluating->SetFitness(fitness);

    // load next genome
    if (finished) return;

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
    end_controller_time = time + evaluation_time;
}
