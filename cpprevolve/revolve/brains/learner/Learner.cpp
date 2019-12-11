//
// Created by matteo on 12/6/19.
//

#include "Learner.h"

using namespace revolve;

void Learner::optimize(double time, double /*dt*/)
{
    if (time < end_controller_time) return;

    bool finished = evaluation_counter >= static_cast<long>(n_evaluations);
    if (finished)
    {
        evaluation_reporter->report(evaluation_counter, true, evaluator->fitness());
    }
    else
    {
        std::cout << "Learner evaluation_counter: " << evaluation_counter + 1 << std::endl;
        // first evaluation
        if (evaluation_counter < 0) {
            evaluation_counter = 0;
            this->init_first_controller();
        } else {
            // finalize previous run
            evaluation_counter++;
            double fitness = evaluator->fitness();
            finished = evaluation_counter >= static_cast<long>(n_evaluations);

            evaluation_reporter->report(evaluation_counter, finished, fitness);
            this->finalize_current_controller(fitness);
            std::cout << "Fitness: " << fitness << std::endl;

            // load next genome
            if (finished) {
                this->load_best_controller();
            } else {
                this->init_next_controller();
            }
        }
    }

    evaluator->reset();
    end_controller_time = time + evaluation_time;
}
