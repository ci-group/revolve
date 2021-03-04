//
// Created by fuda on 18-12-20.
//

#include "DifferentialEvo.h"
#include <iomanip>
#include <random>
#include <fstream>
const static Eigen::IOFormat CSVFormat(11, Eigen::DontAlignCols, ", ", ",");

namespace revolve {
    DifferentialEvo::DifferentialEvo(std::unique_ptr<Controller> controller,
                                     Evaluator *evaluator,
                                     EvaluationReporter *reporter,
                                     const DifferentialEvo::DE_Parameters &params,
                                     int seed,
                                     double evaluation_time,
                                     unsigned int n_learning_evaluations,
                                     const std::string &model_name)
            : EA(std::move(controller), evaluator, reporter,
                 params.EA_params, seed, evaluation_time,
                 n_learning_evaluations,
                 model_name) {
        std::cout << "[DiffEvo] constructor" << std::endl;
        this->DE_Param = params;
        this->F = DE_Param.F;
        this->CR = DE_Param.CR;
        this->type = DE_Param.type;
        this->n_parents = DE_Param.n_parents;
        this->elitism = DE_Param.elitism;

        std::vector<std::string> de_types{"de", "ade", "revde", "dex3"};

        assert ((0. <= this->F) && (this->F <= 2.) && "F must be in [0, 2]");
        assert ((0. < this->CR) && (this->CR <= 1.) && "CR must be in (0, 1]");
        assert ((this->elitism>=0.) && (this->elitism < 1.0) && "Elitism must be in [0, 1)");
        assert ((std::find(de_types.begin(), de_types.end(), this->type) != de_types.end())
                && "type must be one in {de, dex3, ade, revde}");


        int n_params = this->get_genome().size();

        std::vector<double> initial_samples = randomNum->randVectd(EA_Params.min_weight, EA_Params.max_weight,
                                                                   n_params*EA_Params.population_size);

        std::vector<double> genome(n_params);

        for (int u = 0; u < EA_Params.population_size; u++) {
            for (int v = 0; v < n_params; v++)
                genome[v] = initial_samples[v+u];

            Individual::indPtr ind(new Individual());
            ind->setGenome(genome);
            population.push_back(ind);
        }
        std::cout << "[DiffEvo] population initialized" << std::endl;
    }

    DifferentialEvo::~DifferentialEvo()= default;

    void DifferentialEvo::epoch() {
        /** NOVELTY **/
        if (DE_Param.novelty_ratio > 0.) {
            if (Novelty::k_value >= population.size())
                Novelty::k_value = int(population.size() / 2);
            else Novelty::k_value = DE_Param.novelty_k_value;

            std::vector<Eigen::VectorXd> pop_desc;
            for (const auto &ind : population)
                pop_desc.push_back(ind->descriptor());
            //compute novelty
            for (const auto &ind : population) {
                Eigen::VectorXd ind_desc = ind->descriptor();
                double ind_nov = Novelty::sparseness(Novelty::distances(ind_desc, archive, pop_desc));
                ind->setNovelty(ind_nov);
            }

            //update archive
            for (const auto &ind : population) {
                Eigen::VectorXd ind_desc = ind->descriptor();
                double ind_nov = ind->get_ctrl_novelty();
                Novelty::update_archive(ind_desc, ind_nov, archive, randomNum);
            }
        }

        this->selection();
    }

    void DifferentialEvo::selection() {
        this->population.insert(this->population.end(), pop_s.begin(), pop_s.end());

        std::vector<int> pop_ind(population.size());
        std::size_t n(0);
        std::generate(std::begin(pop_ind), std::end(pop_ind), [&]{ return n++; });

        std::sort(  std::begin(pop_ind),
                    std::end(pop_ind),
                    [&](int i1, int i2) {
            return this->population[i1]->getFitness() > this->population[i2]->getFitness(); } );

        std::ofstream gen_fitness;
        gen_fitness.open(this->output_dir+"/gen_best_fitness.txt", std::ios::app);
        gen_fitness<< std::setprecision(std::numeric_limits<long double>::digits10 +1)
                   << this->population[pop_ind[0]]->getFitness() << std::endl;
        gen_fitness.close();

        std::ofstream gen_genome;
        gen_genome.open(this->output_dir+"/gen_best_genome.txt", std::ios::app);
        gen_genome<< std::setprecision(std::numeric_limits<long double>::digits10 +1)
                  << this->population[pop_ind[0]]->genome.format(CSVFormat) << std::endl;
        gen_genome.close();

        pop_s.clear();
        for (int j = 0; j < EA_Params.population_size; j++) {
            pop_s.push_back(this->population[pop_ind[j]]);
        }
    }

    void DifferentialEvo::init_next_pop() {

        auto [new_samples, parent_ind] = recombination();

        int n_param = population[0]->get_ctrl_genome().size();
        std::vector<double> genome(n_param);

        population.clear();
        for (int i = 0; i < new_samples.cols(); i++) {

            for (int j = 0; j < n_param; j++)
                genome[j] = new_samples(j, i);

            Individual::indPtr ind(new Individual());
            ind->setGenome(genome);
            population.push_back(ind);
        }
    }

    std::tuple<Eigen::ArrayXXd, std::vector<std::vector<int>> >  DifferentialEvo::recombination(){
        std::vector<std::vector<int>> parent_ind;

        std::vector<int> pop_ind(pop_s.size());

        Eigen::ArrayXXd genomes(this->get_genome().size(),this->pop_s.size());
        std::vector<Eigen::ArrayXXd> parent_genomes;
        // Prepare for vector permutation
        for (size_t j = 0; j < pop_s.size(); j++) {
            pop_ind[j] = j;
            genomes.col(j) = getIndividual(pop_ind[j])->genome;
        }

        for (int i=0; i<n_parents; i++) {
            parent_ind.push_back(pop_ind);
            parent_genomes.push_back(genomes);

            std::random_shuffle(pop_ind.begin(), pop_ind.end());

            for (size_t j = 0; j < pop_s.size(); j++) {
                genomes.col(j) = getIndividual(pop_ind[j])->genome;
            }
        }

        if (this->type == "de"){
            Eigen::ArrayXXd y_1(this->get_genome().size(),pop_s.size());
            y_1 = (parent_genomes[0] + this->F * (parent_genomes[1] - parent_genomes[2]))
                    .cwiseMax(EA_Params.min_weight).cwiseMin(EA_Params.max_weight);

            if (this->CR < 1.) {
                int shape[]= {static_cast<int>(y_1.rows()), static_cast<int>(y_1.cols())};
                Eigen::ArrayXXd p_1 = this->randomNum->Bernoulli(this->CR, shape).cast<double>();

                y_1 = p_1* y_1 + (1. - p_1) * parent_genomes[0];
            }
            return {y_1, parent_ind};
        }
        else if ((this->type == "revde")) {
            Eigen::ArrayXXd y_1(this->get_genome().size(),pop_s.size());
            Eigen::ArrayXXd y_2(this->get_genome().size(),pop_s.size());
            Eigen::ArrayXXd y_3(this->get_genome().size(),pop_s.size());

            y_1 = (parent_genomes[0] + this->F * (parent_genomes[1] - parent_genomes[2]))
                    .cwiseMax(EA_Params.min_weight).cwiseMin(EA_Params.max_weight);
            y_2 = (parent_genomes[1] + this->F * (parent_genomes[2] - y_1))
                    .cwiseMax(EA_Params.min_weight).cwiseMin(EA_Params.max_weight);
            y_3 = (parent_genomes[2] + this->F * (y_1 - y_2))
                    .cwiseMax(EA_Params.min_weight).cwiseMin(EA_Params.max_weight);

//        uniform crossover
            if (this->CR < 1.) {
                int shape[]= {static_cast<int>(y_1.rows()), static_cast<int>(y_1.cols())};
                Eigen::ArrayXXd p_1 = this->randomNum->Bernoulli(this->CR, shape).cast<double>();
                Eigen::ArrayXXd p_2 = this->randomNum->Bernoulli(this->CR, shape).cast<double>();
                Eigen::ArrayXXd p_3 = this->randomNum->Bernoulli(this->CR, shape).cast<double>();
                y_1 = p_1 * y_1 + (1. - p_1) * parent_genomes[0];
                y_2 = p_2 * y_2 + (1. - p_2) * parent_genomes[1];
                y_3 = p_3 * y_3 + (1. - p_3) * parent_genomes[2];
            }

            Eigen::ArrayXXd population(this->get_genome().size(),pop_s.size()*3);
            population << y_1 , y_2 , y_3;
            return {population, parent_ind};
        }
        else if (this->type == "ade") {
            Eigen::ArrayXXd y_1(this->get_genome().size(),pop_s.size());
            Eigen::ArrayXXd y_2(this->get_genome().size(),pop_s.size());
            Eigen::ArrayXXd y_3(this->get_genome().size(),pop_s.size());

            y_1 = (parent_genomes[0] + this->F * (parent_genomes[1] - parent_genomes[2]))
                    .cwiseMax(EA_Params.min_weight).cwiseMin(EA_Params.max_weight);
            y_2 = (parent_genomes[1] + this->F * (parent_genomes[2] - parent_genomes[0]))
                    .cwiseMax(EA_Params.min_weight).cwiseMin(EA_Params.max_weight);
            y_3 = (parent_genomes[2] + this->F * (parent_genomes[0] - parent_genomes[1]))
                    .cwiseMax(EA_Params.min_weight).cwiseMin(EA_Params.max_weight);

//        uniform crossover
            if (this->CR < 1.) {
                int shape[]= {static_cast<int>(y_1.rows()), static_cast<int>(y_1.cols())};
                Eigen::ArrayXXd p_1 = this->randomNum->Bernoulli(this->CR, shape).cast<double>();
                Eigen::ArrayXXd p_2 = this->randomNum->Bernoulli(this->CR, shape).cast<double>();
                Eigen::ArrayXXd p_3 = this->randomNum->Bernoulli(this->CR, shape).cast<double>();
                y_1 = p_1 * y_1 + (1. - p_1) * parent_genomes[0];
                y_2 = p_2 * y_2 + (1. - p_2) * parent_genomes[1];
                y_3 = p_3 * y_3 + (1. - p_3) * parent_genomes[2];
            }

            Eigen::ArrayXXd population(this->get_genome().size(),pop_s.size()*3);
            population << y_1 , y_2 , y_3;
            return {population, parent_ind};
        }
        if (this->type == "dex3") {
            Eigen::ArrayXXd y_1(this->get_genome().size(),pop_s.size());
            Eigen::ArrayXXd y_2(this->get_genome().size(),pop_s.size());
            Eigen::ArrayXXd y_3(this->get_genome().size(),pop_s.size());

            y_1 = (parent_genomes[0] + this->F * (parent_genomes[1] - parent_genomes[2]))
                    .cwiseMax(EA_Params.min_weight).cwiseMin(EA_Params.max_weight);
            y_2 = (parent_genomes[0] + this->F * (parent_genomes[3] - parent_genomes[4]))
                    .cwiseMax(EA_Params.min_weight).cwiseMin(EA_Params.max_weight);
            y_3 = (parent_genomes[0] + this->F * (parent_genomes[5] - parent_genomes[6]))
                    .cwiseMax(EA_Params.min_weight).cwiseMin(EA_Params.max_weight);

//        uniform crossover
            if (this->CR < 1.) {
                int shape[]= {static_cast<int>(y_1.rows()), static_cast<int>(y_1.cols())};
                Eigen::ArrayXXd p_1 = this->randomNum->Bernoulli(this->CR, shape).cast<double>();
                Eigen::ArrayXXd p_2 = this->randomNum->Bernoulli(this->CR, shape).cast<double>();
                Eigen::ArrayXXd p_3 = this->randomNum->Bernoulli(this->CR, shape).cast<double>();
                y_1 = p_1 * y_1 + (1. - p_1) * parent_genomes[0];
                y_2 = p_2 * y_2 + (1. - p_2) * parent_genomes[1];
                y_3 = p_3 * y_3 + (1. - p_3) * parent_genomes[2];
            }

            Eigen::ArrayXXd population(this->get_genome().size(),pop_s.size()*3);
            population << y_1 , y_2 , y_3;
            return {population, parent_ind};
        }
        else {
            throw std::runtime_error("Wrong name of the differential mutation!");
        }
    }

    bool DifferentialEvo::is_finish() {
        int maxNbrEval = EA_Params.max_eval;
        return _is_finish || numberEvaluation >= maxNbrEval;
    }

    bool DifferentialEvo::finish_eval() {
        return EA::finish_eval();
    }
}