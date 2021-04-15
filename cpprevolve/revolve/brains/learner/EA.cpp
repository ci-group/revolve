//
// Created by fuda on 11/23/20.
//

#include "../controller/DifferentialCPG.h"
#include "EA.h"
#include <memory>
using namespace revolve;
const static Eigen::IOFormat CSVFormat(11, Eigen::DontAlignCols, ", ", ",");

EA::EA(std::unique_ptr<Controller> controller,
       Evaluator *evaluator,
       EvaluationReporter *reporter,
       const EA::Parameters &params,
       int seed,
       const double evaluation_time,
       unsigned int n_learning_evaluations,
       const std::string& model_name)
        : Learner(evaluator, reporter, evaluation_time, n_learning_evaluations)
        , _controller(std::move(controller))
//        , params(params)
//        , population(nullptr)
{
    max_learning_evaluations = int(n_learning_evaluations);
    EA_Params = params;
    this->output_dir = "./experiments/learner_knn/"+model_name;

    revolve::RandNum rn(seed);
    this->set_randomNum(std::make_shared<revolve::RandNum>(rn));

    assert(this->_controller && "EA: passed null controller");
    switch (this->_controller->controller_type)
    {
        case revolve::Controller::DIFFERENTIAL_CPG:
            EA_Params.max_weight = 1.0;
            EA_Params.min_weight = 0.0;

            load_genome = [this](Eigen::VectorXd weights) {
                std::vector<double> std_weights(weights.size());
                for (size_t j = 0; j < weights.size(); j++) {
                    std_weights[j] = weights(j);
                }

                auto *temp_controller = dynamic_cast<::revolve::DifferentialCPG*>(this->_controller->into_DifferentialCPG());
                temp_controller->set_connection_weights(std_weights);
            };

            get_genome = [this]() {
                auto *controller = dynamic_cast<::revolve::DifferentialCPG*>(this->_controller->into_DifferentialCPG());
                const std::vector<double> &weights = controller->get_connection_weights();
                Eigen::VectorXd eigen_weights(weights.size());
                for (size_t j = 0; j < weights.size(); j++) {
                    eigen_weights(j) = weights.at(j);
                }

                return eigen_weights;
            };
            break;
        default:
            std::cerr << "Controller not supported" << std::endl;
            throw std::runtime_error("Controller not supported");
    }
}

void EA::init_first_controller()
{
    current_Ind = population.begin();
    this->set_current_Ind_Index(0);
    this->set_generation(0);

    //TODO load genome in controller
    this->load_genome((*current_Ind)->genome);

    std::cout<<"[EA] initialized first controller"<<std::endl;
}

void EA::init_next_controller()
{
    std::cout<<"[EA] start update" <<std::endl;
    // load next genome
    current_Ind++;
    current_Ind_Index++;

    // Finished a generation
    if (current_Ind == population.end())
    {
        std::cout<<"###### Generation: \t" << this->generation << "\t Pop size: " << this->population.size()<<
                 "\n###### Best ind:\t"<< this->best_Ind << "\t Fitness: " << this->best_fitness <<
                 "\n###### Genome:  \t";
        for (auto g : this->getIndividual(this->best_Ind)->get_ctrl_genome()) {
            std::cout << g << ", ";
        };
        std::cout<<std::endl;

        this->epoch();
        this->init_next_pop();
        this->incr_generation();
        this->set_current_Ind_Index(0);
        current_Ind = population.begin();
    }
    if(this->is_finish()){
        if(EA_Params.verbose)
        {
            std::cout << "---------------------" << std::endl;
            std::cout << "Evolution is Finished" << std::endl;
            std::cout << "---------------------" << std::endl;
        }
        exit(0);
    }
    const Eigen::VectorXd &genome = (*current_Ind)->genome;
    this->load_genome(genome);
    std::cout <<"[EA] end update" << std::endl;
}

void EA::finalize_current_controller(double fitness)
{
    (*current_Ind)->setFitness(fitness);

    if(fitness>best_fitness)
    {
        this->best_fitness = fitness;
        this->best_genome = (*current_Ind)->genome;
        this->best_Ind = current_Ind_Index;
    }

    //  Write fitness to file
    std::ofstream fitness_file;
    std::cout << "Fitness output folder " << this->output_dir << std::endl;
    fitness_file.open(this->output_dir+"/fitnesses.txt", std::ios::app);
    fitness_file<< std::setprecision(std::numeric_limits<long double>::digits10 +1)
                <<fitness << std::endl;
    fitness_file.close();

    // Write genotype to file
    std::ofstream genolog(this->output_dir+"/genotype.log", std::ios::app);
    if (genolog.is_open())
    {
        genolog << (*current_Ind)->genome.format(CSVFormat) <<std::endl;
        genolog.close();
    }

}

void EA::load_best_controller()
{
    //TODO load best genome into controller
    this->load_genome(this->best_genome);
}




/// ############## virtual part for different EA implementations ##############
EA::~EA()
{
    randomNum.reset();
//    parameters.reset();
    for(auto& ind : population)
        ind.reset();
}
void EA::setSettings(const RandNum::Ptr &rn)
{
//    parameters = param;
    randomNum = rn;
}
void EA::epoch(){
    evaluation();
    selection();
}
void EA::init_next_pop(){
    replacement();
    crossover();
    mutation();
}
Individual::indPtr EA::getIndividual(size_t index) const
{
    return population[index];
}
