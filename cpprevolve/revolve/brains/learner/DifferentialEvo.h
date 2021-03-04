//
// Created by fuda on 18-12-20.
//

#pragma once
#include <string>
//#include <iostream>
#include "Learner.h"
#include "Evaluator.h"
#include "EA.h"

#ifndef REVOLVE_DIFFERENTIALEVO_H
#define REVOLVE_DIFFERENTIALEVO_H

namespace revolve {
    class DifferentialEvo : public EA {
    public:
        struct DE_Parameters {
            std::string type = "de";

            double F = 1.0;
            double CR = 0.5;
            double elitism = 0.;
            int n_parents = 3;

            int novelty_k_value = 15;
            double novelty_ratio = 1.;
//            double novelty_decrement = 0.05;
//            double novelty_threshold = 0.9;
//            double novelty_archive_probability = 0.4;

            EA::Parameters EA_params;
        };

        explicit DifferentialEvo(std::unique_ptr<Controller> controller,
                                 Evaluator *evaluator,
                                 EvaluationReporter *reporter,
                                 const DifferentialEvo::DE_Parameters &params,
                                 int seed,
                                 double evaluation_time,
                                 unsigned int n_learning_evaluations,
                                 const std::string &model_name);

        Controller *controller() override { return _controller.get(); }

        ~DifferentialEvo();

        void epoch() override;

        void init_next_pop() override;

        void selection() override;

        std::tuple<Eigen::ArrayXXd, std::vector<std::vector<int>>> recombination();

        bool is_finish() override;

        bool finish_eval() override;

        const std::vector<Eigen::VectorXd> &get_archive() { return archive; }

    protected:
        std::vector<Individual::indPtr> pop_s;
        std::string type;
        bool _is_finish = false;
        std::vector<Eigen::VectorXd> archive;
        DifferentialEvo::DE_Parameters DE_Param;
        double F;
        double CR;
        int n_parents;
        double elitism;
    };
};

#endif //REVOLVE_DIFFERENTIALEVO_H
