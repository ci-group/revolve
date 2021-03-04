//
// Created by fuda on 11/23/20.
//

#pragma once
#ifndef REVOLVE_EA_H
#define REVOLVE_EA_H

#include "Learner.h"
#include "Evaluator.h"
#include <Eigen/Core>
#include <chrono>
#include "EA_misc/RandNum.h"
#include "EA_misc/Novelty.h"

//#include "multineat/Genome.h"
//#include <multineat/Population.h>

namespace revolve
{
    class Individual
    {
    public:
        Individual(){};
        typedef std::shared_ptr<Individual> indPtr;
        Eigen::VectorXd genome;
        double fitness = -std::numeric_limits<double>::infinity();
        double novelty;

        void setFitness(double value){fitness = value;};
        void setNovelty(double ind_nov){novelty = ind_nov;}
        void setGenome(std::vector<double> gen){
//            this->genome = Eigen::VectorXd::Map(gen.data(), gen.size(), 0);
            Eigen::VectorXd V(gen.size());
            for (int i=0; i<gen.size(); ++i){
                V(i) = gen[i];
            }
            genome = V;
        };
        double getFitness() const{return fitness;};
        double get_ctrl_novelty() const{return novelty;};
        std::vector<double> get_ctrl_genome(){
            std::vector<double> vec(genome.data(), genome.data() + genome.size());
            return  vec;
        }
        Eigen::VectorXd descriptor(){
//            Eigen::VectorXd desc(3);
//            desc << 0.0, 0.0, 0.0;
            return genome;
        };
    protected:
    };


    typedef std::chrono::high_resolution_clock hr_clock;
    class EA : public Learner
    {
    public:
        struct Parameters {
            bool verbose = false;
            int population_size = 10;
            int max_eval = 300;
            double max_weight = 1.0;
            double min_weight = 0.0;
        };

    /// \brief Constructor
    explicit  EA(
            std::unique_ptr<Controller> controller,
            Evaluator *evaluator,
            EvaluationReporter *reporter,
            const EA::Parameters &params,
            int seed,
            double evaluation_time,
            unsigned int n_learning_evaluations,
            const std::string& model_name);

    /// \brief Destructor
    ~EA();

    Controller *controller() override
    { return _controller.get(); }

    void init_first_controller() override;
    void init_next_controller() override;
    void finalize_current_controller(double fitness) override;
    void load_best_controller() override;


    protected:
        EA::Parameters EA_Params;
        std::vector<Individual::indPtr> population;
        std::vector<Individual::indPtr>::iterator current_Ind;
//        Eigen::VectorXd current_genome_evaluating;
        double best_fitness = -std::numeric_limits<double>::infinity();
        Eigen::VectorXd best_genome;
        int max_learning_evaluations;

        /// \brief ptr to the current robot controller
        std::unique_ptr<Controller> _controller;

        /// \brief function to load a genome into a controller
        std::function<void(Eigen::VectorXd)> load_genome;

        /// \brief function to turn the controller into a sample
        std::function<Eigen::VectorXd()> get_genome;


    /// ############## virtual part for different EA implementations ##############
    public:
        typedef std::unique_ptr<EA> Ptr;
        typedef std::unique_ptr<const EA> ConstPtr;
        typedef EA::Ptr (Factory)(const RandNum::Ptr&);

        std::vector<int> popNextIndNumbers;
        /// This method initilizes setting for EA and random number generator seed
        void setSettings(const RandNum::Ptr &rn);
        /// This method sets the fitness value of an individual
        virtual void setObjectives(size_t indIndex, const double &objectives)
        {
            current_Ind_Index = indIndex;
            population[indIndex]->setFitness(objectives);
        }

        /**
         * @brief Epoch method is called at the end of each generation
         */
        virtual void epoch();
        /**
         * @brief Initialisation of the population for next generation. Called at the end of each generation after the epoch function.
         */
        virtual void init_next_pop();
        /**
         * @brief ending condition of the algorithm
         * @return true if ending condition is meet
         */
        virtual bool is_finish(){
//            int maxGen = max_learning_evaluations;
            return generation >= max_learning_evaluations;
        }
        /**
         * @brief ending condition of the evaluation. This condition is added with OR to the default condition the time limit.
         * @return
         */
        virtual bool finish_eval(){
            return false;
        }

        void incr_generation(){generation++;}
        //GETTERS & SETTERS
        Individual::indPtr getIndividual(size_t index) const;
        size_t getPopSize() const {return population.size();}
        const std::vector<Individual::indPtr> &get_population() const {return population;}
        const EA::Parameters &get_parameters() const {return EA_Params;}
        const RandNum::Ptr get_randomNum() const {return randomNum;}
        int get_generation() const {return generation;}
        int get_numberEvaluation() const {return numberEvaluation;}
        std::chrono::nanoseconds getEvalCompTime() const {
            return std::chrono::duration_cast<std::chrono::nanoseconds>
                    (endEvalTime - startEvalTime);
        }

        void set_randomNum(const RandNum::Ptr& rn){randomNum = rn;}
        void set_generation(int gen){generation = gen;}
        void set_current_Ind_Index(int index){current_Ind_Index = index;}
        void set_startEvalTime(const hr_clock::time_point& t){startEvalTime = t;}
        void set_endEvalTime(const hr_clock::time_point& t){endEvalTime = t;}
    protected:
        /// This method initilizes a population of genomes
        virtual void evaluation(){}  // This is now only used by NEAT but can also be done for the other genomes. However, by passing the update function to the EA different EA objects can contain different scenarios making the plugin more flexible.
        virtual void selection(){}  	// selection operator
        virtual void replacement(){}		// replacement operator
        virtual void mutation(){}		// mutation operator
        virtual void crossover(){}      //crossover
        virtual void end(){}				// last call to the EA, when simulation stops

        ///set the environment type, evolution type...

        ///random number generator for EA
        RandNum::Ptr randomNum;
        int generation = 0;
        int numberEvaluation = 0;
        int current_Ind_Index = 0;
        int best_Ind = 0;
        hr_clock::time_point startEvalTime;
        hr_clock::time_point endEvalTime;
        std::string output_dir;
    };
}//revolve
#endif //REVOLVE_EA_H
