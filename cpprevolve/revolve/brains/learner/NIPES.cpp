//
// Created by matteo on 8/21/19.
//

#include "NIPES.h"

#include <utility>
#include "../controller/DifferentialCPG.h"
#include "EA.h"

namespace revolve {

std::map<int, std::string> IPOPCMAStrategy::scriterias = {{cma::CONT,         "OK"},
                                                          {cma::AUTOMAXITER,  "The automatically set maximal number of iterations per run has been reached"},
                                                          {cma::TOLHISTFUN,   "[Success] The optimization has converged"},
                                                          {cma::EQUALFUNVALS, "[Partial Success] The objective function values are the same over too many iterations, check the formulation of your objective function"},
                                                          {cma::TOLX,         "[Partial Success] All components of covariance matrix are very small (e.g. < 1e-12)"},
                                                          {cma::TOLUPSIGMA,   "[Error] Mismatch between step size increase and decrease of all eigenvalues in covariance matrix. Try to restart the optimization."},
                                                          {cma::STAGNATION,   "[Partial Success] Median of newest values is not smaller than the median of older values"},
                                                          {cma::CONDITIONCOV, "[Error] The covariance matrix's condition numfber exceeds 1e14. Check out the formulation of your problem"},
                                                          {cma::NOEFFECTAXIS, "[Partial Success] Mean remains constant along search axes"},
                                                          {cma::NOEFFECTCOOR, "[Partial Success] Mean remains constant in coordinates"},
                                                          {cma::MAXFEVALS,    "The maximum number of function evaluations allowed for optimization has been reached"},
                                                          {cma::MAXITER,      "The maximum number of iterations specified for optimization has been reached"},
                                                          {cma::FTARGET,      "[Success] The objective function target value has been reached"}};

bool IPOPCMAStrategy::reach_ftarget() {
    cma::CMAES_LOG_IF(cma::INFO, !_parameters.quiet()) << "Best fitness : " << best_fitnesses.back() << std::endl;

    if (_parameters.get_ftarget() != std::numeric_limits<double>::infinity()) {
        if (best_fitnesses.back() <= _parameters.get_ftarget()) {
            std::stringstream sstr;
            sstr << "stopping criteria fTarget => fvalue=" << best_fitnesses.back() << " / ftarget="
                 << _parameters.get_ftarget();
            log_stopping_criterias.push_back(sstr.str());
            cma::CMAES_LOG_IF(cma::INFO, !_parameters.quiet()) << sstr.str() << std::endl;
            return true;
        }
    }
    return false;
}

bool IPOPCMAStrategy::pop_desc_stagnation() {
    std::vector<Eigen::VectorXd> descriptors;
    for (const auto &ind: _pop)
        descriptors.push_back(std::dynamic_pointer_cast<Individual>(ind)->descriptor());

    Eigen::VectorXd mean = Eigen::VectorXd::Zero(_pop[0]->genome.size());
    for (Eigen::VectorXd desc : descriptors) {
        mean += desc;
    }
    mean = mean / static_cast<double>(descriptors.size());

    Eigen::VectorXd stddev = Eigen::VectorXd::Zero(_pop[0]->genome.size());
    for (Eigen::VectorXd desc : descriptors)
        stddev += (desc - mean).cwiseProduct(desc - mean);

    bool stop = true;
    for (int i = 0; i < stddev.rows(); i++)
        stop = stop && sqrt(stddev(i / static_cast<double>(descriptors.size() - 1))) <= pop_stag_thres;

    if (stop) {
        std::stringstream sstr;
        sstr << "Stopping : standard deviation of the descriptor population is smaller than " << pop_stag_thres
             << " : " << stddev;
        log_stopping_criterias.push_back(sstr.str());
        cma::CMAES_LOG_IF(cma::INFO, !_parameters.quiet()) << sstr.str() << std::endl;
    }
    return stop;
}

bool IPOPCMAStrategy::pop_fit_stagnation() {
    std::vector<double> fvalues;
    for (const auto &ind : _pop)
        fvalues.push_back(ind->getFitness());


    double mean = 0.0;
    for (double fv : fvalues)
        mean += fv;
    mean = mean / static_cast<double>(fvalues.size());

    double stddev = 0.0;
    for (double fv : fvalues)
        stddev += (fv - mean) * (fv - mean);

    stddev = sqrt(stddev / static_cast<double>(fvalues.size() - 1));
    cma::CMAES_LOG_IF(cma::INFO, !_parameters.quiet()) << "pop standard deviation : " << stddev << std::endl;

    if (stddev <= pop_stag_thres) {
        std::stringstream sstr;
        sstr << "Stopping : standard deviation of the population is smaller than 0.05 : " << stddev;
        log_stopping_criterias.push_back(sstr.str());
        cma::CMAES_LOG_IF(cma::INFO, !_parameters.quiet()) << sstr.str() << std::endl;
        return true;
    } else return false;
}

bool IPOPCMAStrategy::best_sol_stagnation() {
    if (best_fitnesses.size() < len_of_stag)
        return false;
    double mean = 0.0;
    for (size_t i = best_fitnesses.size() - len_of_stag; i < best_fitnesses.size(); i++) {
        mean += best_fitnesses[i];
    }
    mean = mean / static_cast<float>(len_of_stag);
    double stddev = 0.0;
    for (size_t i = best_fitnesses.size() - len_of_stag; i < best_fitnesses.size(); i++) {
        stddev += (best_fitnesses[i] - mean) * (best_fitnesses[i] - mean);
    }
    stddev = sqrt(stddev / static_cast<float>(len_of_stag - 1));

    if (stddev <= 0.05) {
        std::stringstream sstr;

        sstr << "Stopping : standard deviation of the last " << len_of_stag
             << " best fitnesses is smaller than 0.05 : " << stddev;
        log_stopping_criterias.push_back(sstr.str());
        cma::CMAES_LOG_IF(cma::INFO, !_parameters.quiet()) << sstr.str() << std::endl;
        return true;
    } else return false;
}

void IPOPCMAStrategy::eval(const dMat &candidates, const dMat &phenocandidates) {
    // custom eval.
    _solutions.candidates().clear();
    for (Individual::indPtr &r : _pop) {
        dVec x;
        x = r->genome;
        double fvalue = r->getFitness();
        _solutions.candidates().push_back(cma::Candidate(fvalue, x));
    }
    update_fevals(candidates.cols());
}

void IPOPCMAStrategy::tell() {
    ipop_cmaes_t::tell();
    std::vector<double> best_sample;
    best_fitnesses.push_back(best_fitness(best_sample));
    if (novelty_ratio > 0)
        novelty_ratio -= novelty_decr;
    if (best_fitnesses.back() < best_seen_solution.first || best_fitnesses.size() == 1)
        best_seen_solution = std::make_pair(best_fitnesses.back(), best_sample);
    inc_iter();
}

bool IPOPCMAStrategy::stop() {
    reached_ft = reach_ftarget();
    bool ipop_stop = ipop_cmaes_t::stop();
    bool pop_stag = pop_desc_stagnation();
    bool fit_stag = pop_fit_stagnation();
    bool best_sol_stag = false;
    if (len_of_stag > 0)
        best_sol_stag = best_sol_stagnation();

    if (ipop_stop) {
        log_stopping_criterias.push_back(scriterias[_solutions.run_status()]);
    }
    return pop_stag || best_sol_stag || ipop_stop || fit_stag;
}

void IPOPCMAStrategy::reset_search_state() {
    if (elitist_restart)
        _parameters.set_x0(best_seen_solution.second, best_seen_solution.second);

    ipop_cmaes_t::reset_search_state();
    novelty_ratio = start_novelty_ratio;
    best_fitnesses.clear();
}

double IPOPCMAStrategy::best_fitness(std::vector<double> &best_sample) {
    double bf = -std::numeric_limits<double>::infinity();
    for (const auto &ind : _pop) {
        if (bf < ind->getFitness()) {
            bf = ind->getFitness();
            best_sample = ind->get_ctrl_genome();
        }
    }

    return bf;
}

/// ################### ARE: top #################
NIPES::NIPES(std::unique_ptr<Controller> controller,
             Evaluator *evaluator,
             EvaluationReporter *reporter,
             const NIPES::NIPES_Parameters &params,
             int seed,
             double evaluation_time,
             unsigned int n_learning_evaluations,
             const std::string &model_name)
        : EA(std::move(controller), evaluator, reporter,
             params.EA_params, seed, evaluation_time,
             n_learning_evaluations,
             model_name) {

    int lenStag = Nipes_Param.stagnation_length;
    double step_size = Nipes_Param.CMAES_step;
//    double ftarget = Nipes_Param.ftarget;
    bool elitist_restart = Nipes_Param.elitist_restart;
    double novelty_ratio = Nipes_Param.novelty_ratio;
    double novelty_decr = Nipes_Param.novelty_decrement;
    float pop_stag_thres = Nipes_Param.population_stagnation_threshold;

    Novelty::k_value = Nipes_Param.novelty_k_value;
    Novelty::novelty_thr = Nipes_Param.novelty_threshold;
    Novelty::archive_adding_prob = Nipes_Param.novelty_archive_probability;

    int n_params = this->get_genome().size();

    std::vector<double> initial_point = randomNum->randVectd(EA_Params.min_weight, EA_Params.max_weight, n_params);

    double lb[n_params], ub[n_params];
    for (int i = 0; i < n_params; i++) {
        lb[i] = EA_Params.min_weight;
        ub[i] = EA_Params.max_weight;
    }

    geno_pheno_t gp(lb, ub, n_params);

    cma::CMAParameters<geno_pheno_t> cmaParam(initial_point, step_size, EA_Params.population_size,
                                              randomNum->getSeed(), gp);
//    cmaParam.set_ftarget(ftarget);
    cmaParam.set_quiet(!EA_Params.verbose);

    cmaStrategy.reset(new IPOPCMAStrategy([](const double *, const int &) -> double {}, cmaParam));
    cmaStrategy->set_elitist_restart(elitist_restart);
    cmaStrategy->set_length_of_stagnation(lenStag);
    cmaStrategy->set_novelty_ratio(novelty_ratio);
    cmaStrategy->set_novelty_decr(novelty_decr);
    cmaStrategy->set_pop_stag_thres(pop_stag_thres);

    dMat init_samples = cmaStrategy->ask();

    std::vector<double> genome(n_params);

    for (int u = 0; u < EA_Params.population_size; u++) {

        for (int v = 0; v < n_params; v++)
            genome[v] = init_samples(v, u);

        Individual::indPtr ind(new Individual());
        ind->setGenome(genome);
        population.push_back(ind);
    }
    std::cout << "[NIPES] population initialized" << std::endl;
}

NIPES::~NIPES() {
    cmaStrategy.reset();
}

void NIPES::epoch() {
    bool withRestart = Nipes_Param.restart;
    bool incrPop = Nipes_Param.incremental_population;
    bool elitist_restart = Nipes_Param.elitist_restart;

    /** NOVELTY **/
    if (Nipes_Param.novelty_ratio > 0.) {
        if (Novelty::k_value >= population.size())
            Novelty::k_value = population.size() / 2;
        else Novelty::k_value = Nipes_Param.novelty_k_value;

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
    /**/

    cmaStrategy->set_population(population);
    cmaStrategy->eval();
    cmaStrategy->tell();
    bool stop = cmaStrategy->stop();
//    if(cmaStrategy->have_reached_ftarget()){
//        _is_finish = true;
////        return;
//    }

    if (withRestart && stop) {
        if (EA_Params.verbose)
            std::cout << "Restart !" << std::endl;

        cmaStrategy->capture_best_solution(best_run);

        if (incrPop)
            cmaStrategy->lambda_inc();

        cmaStrategy->reset_search_state();
        if (!elitist_restart) {
            cmaStrategy->get_parameters().set_x0(EA_Params.min_weight, EA_Params.max_weight);
        }
    }
}

void NIPES::init_next_pop() {
    int pop_size = cmaStrategy->get_parameters().lambda();

    dMat new_samples = cmaStrategy->ask();

    int n_param = population[0]->get_ctrl_genome().size();
    std::vector<double> genome(n_param);

    population.clear();
    for (int i = 0; i < pop_size; i++) {

        for (int j = 0; j < n_param; j++)
            genome[j] = new_samples(j, i);

        Individual::indPtr ind(new Individual());
        ind->setGenome(genome);
        population.push_back(ind);
    }
}


bool NIPES::is_finish() {
    int maxNbrEval = EA_Params.max_eval;
    return _is_finish || numberEvaluation >= maxNbrEval;
}

bool NIPES::finish_eval() {
    return EA::finish_eval();
}
};