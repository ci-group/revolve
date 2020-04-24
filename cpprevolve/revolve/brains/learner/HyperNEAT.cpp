//
// Created by matteo on 8/21/19.
//

#include "HyperNEAT.h"
#include "../controller/DifferentialCPG.h"

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
    assert(this->_controller && "HyperNEAT: passed null controller");
    switch (this->_controller->controller_type)
    {
        case revolve::Controller::DIFFERENTIAL_CPG:
        load_genome = [this](std::vector<NEAT::Genome>::iterator config_cppn_genome)
                {
                auto *temp_controller = dynamic_cast<::revolve::DifferentialCPG *>(this->_controller.get()->into_DifferentialCPG());
                temp_controller->load_genome_to_controller(*config_cppn_genome);
            };
            break;
        default:
            std::cerr << "Controller not supported" << std::endl;
            throw std::runtime_error("Controller not supported");
    }
}

void HyperNEAT::init_first_controller()
{
    current_specie_evaluating = population->m_Species.begin();
    current_genome_evaluating = current_specie_evaluating->m_Individuals.begin();

    //TODO load genome in controller
    this->load_genome(current_genome_evaluating);
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
    this->load_genome(current_genome_evaluating);
}

void HyperNEAT::finalize_current_controller(double fitness)
{
    current_genome_evaluating->SetFitness(fitness);
    if(fitness>best_fitness)
    {
        this->best_fitness = fitness;
        this->best_genome = current_genome_evaluating;
    }
}

void HyperNEAT::load_best_controller()
{
    //TODO load best genome into controller
//    this->load_genome(current_genome_evaluating);
    this->load_genome(this->best_genome);
}
