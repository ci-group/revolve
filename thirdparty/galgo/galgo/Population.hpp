//=================================================================================================
//                  Copyright (C) 2018 Alain Lanthier - All Rights Reserved  
//                  License: MIT License    See LICENSE.md for the full license.
//                  Original code 2017 Olivier Mallet (MIT License)              
//=================================================================================================

#ifndef POPULATION_HPP
#define POPULATION_HPP

#include <iostream>
#include <fstream>
//#include "opencv2/highgui/highgui.hpp"
//#include "opencv2/core/core.hpp"
#include <sys/time.h>
#include <math.h>

namespace galgo
{

  template <typename T> class Population
  {
    public:
    // nullary constructor
    Population()
    {
    }

    // constructor
    Population(const GeneticAlgorithm <T> &ga);

    // create a population of chromosomes
    void creation(std::string learner_algorithm,
                  size_t current_iteration,
                  size_t switch_num,
                  std::vector< Eigen::VectorXd> samples,
                  std::vector<Eigen::VectorXd> observations);

    // evolve population, get next generation
    void evolution(size_t current_iteration, double gaussian_step_size);

    //get individuals
    std::vector<double> get_individual(int i);

    // access element in current population at position pos
    const CHR <T> &operator()(int pos) const;

    // access element in mating population at position pos
    const CHR <T> &operator[](int pos) const;

    // return iterator to current population beginning
    typename std::vector< CHR < T>>::

    iterator begin();

    // return const iterator to current population beginning
    typename std::vector< CHR < T>>::

    const_iterator cbegin() const;

    // return iterator to current population ending
    typename std::vector< CHR < T>>::

    iterator end();

    // return const iterator to current population ending
    typename std::vector< CHR < T>>::

    const_iterator cend() const;

    // select element at position pos in current population and copy it into mating population
    void select(int pos);

    // set all fitness to positive values
    void adjustFitness();

    // compute fitness sum of current population
    double getSumFitness() const;

    // get worst objective function total result from current population
    double getWorstTotal() const;

    // return population size
    int popsize() const;

    // return mating population size
    int matsize() const;

    // return tournament size
    int tntsize() const;

    // return numero of generation
    int nogen() const;

    // return number of generations
    int nbgen() const;

    // return selection pressure
    double SP() const;

    const GeneticAlgorithm <T> *ga_algo() { return ptr;}

    std::vector<CHR<T>>& get_newpop() { return newpop;}

    std::vector<CHR<T>>& get_curpop() { return curpop;}

    private:
    std::vector< CHR < T>> curpop;               // current population
    std::vector< CHR < T>> matpop;               // mating population
    std::vector< CHR < T>> newpop;               // new population

    const GeneticAlgorithm <T> *ptr = nullptr; // pointer to genetic algorithm
    int nbrcrov;                              // number of cross-over
    int matidx;                               // mating population index

    // elitism => saving best chromosomes in new population
    void elitism();

    // create new population from recombination of the old one
    void recombination(size_t current_iteration, double gaussian_step_size);

    // complete new population randomly
    void completion(size_t current_iteration, double gaussian_step_size);

    // update population (adapting, sorting)
    void updating();

    bool compare_Xd(const Eigen::VectorXd& lhs, const Eigen::VectorXd& rhs)
    {
      return lhs(0) < rhs(0);
    }
  };

  /*-------------------------------------------------------------------------------------------------*/

  // constructor
  template <typename T>
  Population< T >::Population(const GeneticAlgorithm <T> &ga)
  {
    ptr = &ga;
    nbrcrov = (int)ceil(ga.covrate * (ga.popsize - ga.elitpop));

    // adjusting nbrcrov (must be an even number)
    if (nbrcrov % 2 != 0)
    {
      nbrcrov += 1;
    }

    // for convenience, we add elitpop to nbrcrov
    nbrcrov += ga.elitpop;

    // allocating memory
    curpop.resize(ga.popsize);
    matpop.resize(ga.matsize);
  }

  /*-------------------------------------------------------------------------------------------------*/

  // create a population of chromosomes
  template <typename T> void Population< T >::creation(std::string learner_algorithm,
                                                       size_t current_iteration,
                                                       size_t switch_num,
                                                       std::vector< Eigen::VectorXd> samples,
                                                       std::vector< Eigen::VectorXd> observations)
  {
    int start = 0;

    // initializing first chromosome
    if (!ptr->initialSet.empty())
    {
      curpop[0] = std::make_shared< Chromosome< T>>(*ptr);
      curpop[0]->initialize(); //create new chromosome by encoding value to binary
      curpop[0]->evaluate(); //encoding binary to value and calculating fitness
      start++;
    }
    // getting the rest
    #ifdef _OPENMP
    #pragma omp parallel for num_threads(MAX_THREADS)
    #endif

    if(learner_algorithm == "EA")
    {
      for (int i = start; i < ptr->popsize; ++i)
      {
        curpop[i] = std::make_shared< Chromosome< T>>(*ptr);
        curpop[i]->create(i, samples[i]);
        curpop[i]->evaluate0gen(observations[i]); //row 316 in Chromosome.hpp
      }
    }

/////**** the interface to bayesian optimization ****///
    if(learner_algorithm == "BOEA")
    {
      std::cout << "switch_num: " << switch_num << std::endl;
      // load the individuals from BO
      if(current_iteration == switch_num)
      {
        int dimens = samples[0].size(); // curpop[i]->nbgene()
        std::cout << "dimens: " << dimens << std::endl;
        std::vector< Eigen::VectorXd > boea_observations = observations;
        std::cout << " boea_observations.size(): " << boea_observations.size() << std::endl;
        std::sort(boea_observations.begin(), boea_observations.end(), [](const Eigen::VectorXd& lhs, const Eigen::VectorXd& rhs) {return lhs(0) > rhs(0);});
        std::cout << "boea_observations: " << std::endl;
        for (int i = 0; i < boea_observations.size(); i++)
        {
          std::cout << boea_observations[i] << " ";
        }
        std::cout << std::endl;

        std::vector< Eigen::VectorXd > boea_samples(ptr->popsize);
        for (int i = 0; i < ptr->popsize; i++)
        {
          for (int j = 0; j < boea_observations.size(); j++)
          {
            if (boea_observations[i] == observations[j])
            {
              std::cout << "i: " << i << " " << boea_observations[i] << " "
                        << observations[j] << std::endl;
              std::cout << "samples[" << j << "] " << samples[j] << std::endl;
              boea_samples[i] = samples[j];
              std::cout << "boea_samples[" << i << "]: " << boea_samples[i] << std::endl;
            }
          }
        }

        for (int i = start; i < ptr->popsize; ++i)
        {
          curpop[i] = std::make_shared< Chromosome< T>>(*ptr);
          curpop[i]->create(i, boea_samples[i]);
          curpop[i]->evaluate0gen(boea_observations[i]); //row 316 in Chromosome.hpp
        }
      }
      else
      {
        for (int i = start; i < ptr->popsize; ++i)
        {
          curpop[i] = std::make_shared< Chromosome< T>>(*ptr);
          curpop[i]->create(i, samples[i]);
          curpop[i]->evaluate0gen(observations[i]); //row 316 in Chromosome.hpp
        }
      }
    }

    // updating population: sorting chromosomes from best to worst fitness
    this->updating();
  }

  /*-------------------------------------------------------------------------------------------------*/

  // population evolution (selection, recombination, completion, mutation), get next generation
  template <typename T> void Population< T >::evolution(size_t current_iteration, double gaussian_step_size)
  {
    // initializing mating population index
    matidx = 0;

    // selecting mating population
    // curpop[] -> matpop[]
    ptr->Selection(*this);

    // applying elitism if required
    // curpop[] -> newpop[0...elitpop-1]
    this->elitism();

    // crossing-over mating population
    // matpop[] -> newpop[elitpop...nbrcrov-1] // crossover + mutation
    this->recombination(current_iteration, gaussian_step_size);

    // completing new population // only mutation
    // matpop[] -> newpop[nbrcrov...popsize]
    this->completion(current_iteration, gaussian_step_size);

    // moving new population into current population for next generation
    curpop = std::move(newpop);
//    // galgo::CHR< T > &chr
//    std::cout << "nbgene: " << curpop[0]->nbgene() << std::endl;
//    double individual = curpop[1]->get_value(0);
//    std::cout << "curpop.begin(): " << individual << std::endl;

    // updating population, sorting chromosomes from best to worst fitnes
//    this->updating();

//    std::cout << "curpop.begin(): " << curpop[1]->get_value(0) << std::endl;
  }

  template <typename T>
  std::vector<double> Population< T >::get_individual(int i)
  {
    int nbparams = curpop[i]->nbgene();
    std::vector<double> individual(nbparams);
    //get the parameters of i_th individual
    for(int j = 0; j < nbparams; j++)
    {
      individual[j] = curpop[i]->get_value(j);
      std::cout << individual[j] << " ";
    }
    std::cout << std::endl;
    return individual;
  }
  /*-------------------------------------------------------------------------------------------------*/

  // elitism => saving best chromosomes in new population, making a copy of each elit chromosome
  template <typename T> void Population< T >::elitism()
  {
    // (re)allocating new population
    newpop.resize(ptr->popsize);

    if (ptr->elitpop > 0)
    {
      // copying elit chromosomes into new population
      std::transform(curpop.cbegin(),
                     curpop.cend(),
                     newpop.begin(),
                     [](const CHR< T > &chr) -> CHR< T >
                     { return std::make_shared< Chromosome< T>>(*chr); });

      for (size_t i = 0; i < curpop.size(); i++)
      {
        transmit_sigma< T >(*curpop[i], *newpop[i]);
      }
    }
  }

  /*-------------------------------------------------------------------------------------------------*/

  // create new population from recombination of the old one
  template <typename T> void Population< T >::recombination(size_t current_iteration, double gaussian_step_size)
  {
    // creating a new population by cross-over
#ifdef _OPENMP
#pragma omp parallel for num_threads(MAX_THREADS)
#endif

    for (int i = ptr->elitpop; i < nbrcrov; i = i + 2)
    {
      // initializing 2 new chromosome
      newpop[i] = std::make_shared< Chromosome< T>>(*ptr);
      newpop[i + 1] = std::make_shared< Chromosome< T>>(*ptr);

      // crossing-over mating population to create 2 new chromosomes
      ptr->CrossOver(*this, newpop[i], newpop[i + 1]);

      // mutating new chromosomes
      ptr->Mutation(newpop[i], current_iteration, gaussian_step_size);
      ptr->Mutation(newpop[i + 1], current_iteration, gaussian_step_size);

      if (ptr->FixedValue != nullptr)
      {
        ptr->FixedValue(*this, i);
        ptr->FixedValue(*this, i + 1);
      }

      // evaluating new chromosomes
      //std::cout << "Nu_evaluation_re: " << i;
//      newpop[i]->evaluate();
      //std::cout << "Nu_evaluation_re- " << (i + 1);
//      newpop[i + 1]->evaluate();
    }
  }

  /*-------------------------------------------------------------------------------------------------*/

  // complete new population
  template <typename T> void Population< T >::completion(size_t current_iteration, double gaussian_step_size)
  {
#ifdef _OPENMP
#pragma omp parallel for num_threads(MAX_THREADS)
#endif
    for (int i = nbrcrov; i < ptr->popsize; ++i)
    {
      // selecting chromosome randomly from mating population
      int pos = uniform< int >(0, ptr->matsize);
      newpop[i] = std::make_shared< Chromosome< T>>(*matpop[pos]);
      transmit_sigma< T >(*matpop[pos], *newpop[i]);

      // mutating chromosome
      ptr->Mutation(newpop[i], current_iteration, gaussian_step_size);

      if (ptr->FixedValue != nullptr)
      {
        ptr->FixedValue(*this, i);
      }
      //std::cout << "Nu_evaluation_com: " << i;
      // evaluating chromosome
//      newpop[i]->evaluate();
    }
  }

  /*-------------------------------------------------------------------------------------------------*/

  // update population (adapting, sorting)
  template <typename T> void Population< T >::updating()
  {
//    std::cout << "update population: sorting chromosomes from best to worst fitness" << std::endl;
    // adapting population to constraints
    if (ptr->Constraint != nullptr)
    {
      ptr->Adaptation(*this);
    }
    // sorting chromosomes from best to worst fitness
    std::sort(curpop.begin(), curpop.end(), [](const CHR<T>& chr1, const CHR<T>& chr2)->bool{return chr1->fitness > chr2->fitness;});
  }

  /*-------------------------------------------------------------------------------------------------*/

  // access element in current population at position pos
  template <typename T>
  const CHR <T> &Population< T >::operator()(int pos) const
  {
#ifndef NDEBUG
    if (pos > ptr->popsize - 1)
    {
      throw std::invalid_argument(
          "Error: in galgo::Population<T>::operator()(int), exceeding current population memory.");
    }
#endif

    return curpop[pos];
  }

  /*-------------------------------------------------------------------------------------------------*/

  // access element in mating population at position pos
  template <typename T>
  const CHR <T> &Population< T >::operator[](int pos) const
  {
#ifndef NDEBUG
    if (pos > ptr->matsize - 1)
    {
      throw std::invalid_argument(
          "Error: in galgo::Population<T>::operator[](int), exceeding mating population memory.");
    }
#endif

    return matpop[pos];
  }

  /*-------------------------------------------------------------------------------------------------*/

  // return iterator to current population beginning
  template <typename T> inline typename std::vector< CHR < T>>

  ::iterator Population< T >::begin()
  {
    return curpop.begin();
  }

  /*-------------------------------------------------------------------------------------------------*/

  // return const iterator to current population beginning
  template <typename T> inline typename std::vector< CHR < T>>

  ::const_iterator Population< T >::cbegin() const
  {
    return curpop.cbegin();
  }

  /*-------------------------------------------------------------------------------------------------*/

  // return iterator to current population ending
  template <typename T> inline typename std::vector< CHR < T>>

  ::iterator Population< T >::end()
  {
    return curpop.end();
  }

  /*-------------------------------------------------------------------------------------------------*/

  // return const iterator to current population ending
  template <typename T> inline typename std::vector< CHR < T>>

  ::const_iterator Population< T >::cend() const
  {
    return curpop.cend();
  }

  /*-------------------------------------------------------------------------------------------------*/

  // select element at position pos in current population and copy it into mating population
  template <typename T> inline void Population< T >::select(int pos)
  {
#ifndef NDEBUG
    if (pos > ptr->popsize - 1)
    {
      throw std::invalid_argument(
          "Error: in galgo::Population<T>::select(int), exceeding current population memory.");
    }
    if (matidx == ptr->matsize)
    {
      throw std::invalid_argument(
          "Error: in galgo::Population<T>::select(int), exceeding mating population memory.");
    }
#endif

    matpop[matidx] = curpop[pos];
    matidx++;
  }

  /*-------------------------------------------------------------------------------------------------*/

  // set all fitness to positive values (used in RWS and SUS selection methods)
  template <typename T> void Population< T >::adjustFitness()
  {
    // getting worst population fitness
    double worstFitness = curpop.back()->fitness;

    if (worstFitness < 0)
    {
      // getting best fitness
      double bestFitness = curpop.front()->fitness;
      // case where all fitness are equal and negative
      if (worstFitness == bestFitness)
      {
        std::for_each(curpop.begin(), curpop.end(), [](CHR< T > &chr) -> void
        { chr->fitness *= -1; });
      }
      else
      {
        std::for_each(curpop.begin(),
                      curpop.end(),
                      [worstFitness](CHR< T > &chr) -> void
                      { chr->fitness -= worstFitness; });
      }
    }
  }

  /*-------------------------------------------------------------------------------------------------*/

  // compute population fitness sum (used in TRS, RWS and SUS selection methods)
  template <typename T> inline double Population< T >::getSumFitness() const
  {
    return std::accumulate(curpop.cbegin(), curpop.cend(), 0.0, [](
        double sum,
        const CHR< T > &chr) -> double
    { return sum + chr->fitness; });
  }

  /*-------------------------------------------------------------------------------------------------*/

  // get worst objective function total result from current population (used in constraint(s) adaptation)
  template <typename T> inline double Population< T >::getWorstTotal() const
  {
    auto it = std::min_element(curpop.begin(), curpop.end(), [](
        const CHR< T > &chr1,
        const CHR< T > &chr2) -> bool
    { return chr1->getTotal() < chr2->getTotal(); });
    return (*it)->getTotal();
  }

  /*-------------------------------------------------------------------------------------------------*/

  // return population size
  template <typename T> inline int Population< T >::popsize() const
  {
    return ptr->popsize;
  }

  /*-------------------------------------------------------------------------------------------------*/

  // return mating population size
  template <typename T> inline int Population< T >::matsize() const
  {
    return ptr->matsize;
  }

  /*-------------------------------------------------------------------------------------------------*/

  // return tournament size
  template <typename T> inline int Population< T >::tntsize() const
  {
    return ptr->tntsize;
  }

  /*-------------------------------------------------------------------------------------------------*/

  // return numero of generation
  template <typename T> inline int Population< T >::nogen() const
  {
    return ptr->nogen;
  }


  /*-------------------------------------------------------------------------------------------------*/

  // return number of generations
  template <typename T> inline int Population< T >::nbgen() const
  {
    return ptr->nbgen;
  }

  /*-------------------------------------------------------------------------------------------------*/

  // return selection pressure
  template <typename T> inline double Population< T >::SP() const
  {
    return ptr->SP;
  }

  //=================================================================================================

}

#endif


