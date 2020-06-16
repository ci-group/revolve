//=================================================================================================
//                  Copyright (C) 2018 Alain Lanthier - All Rights Reserved  
//                  License: MIT License    See LICENSE.md for the full license.
//                  Original code 2017 Olivier Mallet (MIT License)              
//=================================================================================================

#ifndef CHROMOSOME_HPP
#define CHROMOSOME_HPP

namespace galgo
{

  //=================================================================================================

  template <typename T> class Chromosome
  {
    public:
    // constructor
    Chromosome(const GeneticAlgorithm <T> &ga);

    // copy constructor
    Chromosome(const Chromosome< T > &rhs);

    // create new chromosome
    void create(int num_in_pop, Eigen::VectorXd indiv);

    // create new chromosome
//    void create();

    // initialize chromosome
    void initialize();

    // evaluate chromosome
    void evaluate();

    // evaluate 0 generations chromosome
    void evaluate0gen(Eigen::VectorXd observations);

    //get the number of generations
    int get_ga_nogen() const;

    // reset chromosome
    void reset();

    // set or replace kth gene by a new one
    void setGene(int k);

    // initialize or replace kth gene by a know value
    void initGene(int k, T value);

    // add bit to chromosome
    void addBit(char bit);

    // initialize or replace an existing chromosome bit
    void setBit(char bit, int pos);

    // flip an existing chromosome bit
    void flipBit(int pos);

    // get chromosome bit
    char getBit(int pos) const;

    // initialize or replace a portion of bits with a portion of another chromosome
    void setPortion(
        const Chromosome< T > &x,
        int start,
        int end);

    // initialize or replace a portion of bits with a portion of another chromosome
    void setPortion(
        const Chromosome< T > &x,
        int start);

    // get parameter value(s) from chromosome
    const std::vector< T > &getParam() const;

    // get objective function result
    const std::vector< double > &getResult() const;

    // get the total sum of all objective function(s) result
    double getTotal() const;

    // get constraint value(s)
    const std::vector< double > getConstraint() const;

    // return chromosome size in number of bits
    int size() const;

    // return number of chromosome bits to mutate
    double mutrate() const;

    const MutationInfo <T> &mutinfo() const;

    double recombination_ratio() const;

    // return number of genes in chromosome
    int nbgene() const;

    // return numero of generation this chromosome belongs to
    int nogen() const;

    // return lower bound(s)
    const std::vector< T > &lowerBound() const;

    // return upper bound(s)
    const std::vector< T > &upperBound() const;

    T get_value(int k) const;

    double get_sigma(int k) const;

    long get_sigma_iteration(int k) const;

    void sigma_update(
        int k,
        double new_sigma)
    {
      _sigma_iteration[k]++;
      _sigma[k] = new_sigma;
    }

    private:
    std::vector< T > param;        // estimated parameter(s)
    std::vector< double > result;  // chromosome objective function(s) result
    std::string chr;               // string of bits representing chromosome
    const GeneticAlgorithm <T> *ptr = nullptr; //pointer to genetic algorithm
    ///******* new **********///
    std::ifstream infile;
    std::ifstream numgens;
//    std::vector< double > indiv;
    std::vector< double > _sigma;           // stddev per parameter
    std::vector< long > _sigma_iteration;   //number of time _sigma was updated

    int clusterCount = 10; //pop_size
    int dimens = 20; //dimensions

    public:
    double fitness;        // chromosome fitness, objective function(s) result that can be modified (adapted to constraint(s), set to positive values, etc...)

    private:
    double total;          // total sum of objective function(s) result
    int chrsize;           // chromosome size (in number of bits)
    int numgen;            // numero of generation
  };

  /*-------------------------------------------------------------------------------------------------*/

  // constructor
  template <typename T>
  Chromosome< T >::Chromosome(const GeneticAlgorithm <T> &ga)
  {
    param.resize(ga.nbparam);
    _sigma.resize(ga.nbparam);
    _sigma_iteration.resize(ga.nbparam);

    ptr = &ga;
    chrsize = ga.nbbit;
    numgen = ga.nogen;
  }

  /*-------------------------------------------------------------------------------------------------*/

  // copy constructor
  template <typename T> Chromosome< T >::Chromosome(const Chromosome< T > &rhs)
  {
    param = rhs.param;
    _sigma = rhs._sigma;
    _sigma_iteration = rhs._sigma_iteration;

    result = rhs.result;
    chr = rhs.chr;
    ptr = rhs.ptr;

    // re-initializing fitness to its original value
    fitness = rhs.total;
    total = rhs.total;
    chrsize = rhs.chrsize;
    numgen = rhs.numgen;
  }

  /*-------------------------------------------------------------------------------------------------*/
  // create new chromosome   //called in row 171 population.hpp
  template <typename T> inline void Chromosome< T >::create(int num_in_pop, Eigen::VectorXd indiv)
  {
    chr.clear();
    // pass MaxIndivPerCluster to param
    int j(0);
    for (const auto &x : ptr->param) // for(0 : dimensions)
    {
      param[j] = indiv[j];
//      std::cout << param[j] << ", ";

      T newvalue = (T) indiv[j];
      initGene(j, newvalue);

      _sigma[j] = 0.0;
      _sigma_iteration[j] = 0;
      j++;
    }
  }

  // create new chromosome
//  template <typename T>
//  inline void Chromosome<T>::create()
//  {
//    chr.clear();
//
//    int i(0);
//    for (const auto& x : ptr->param)
//    {
//      // encoding parameter random value
//      std::string str = x->encode();
//      chr.append(str);
//
//      _sigma[i] = 0.0;
//      _sigma_iteration[i] = 0;
//
//      i++;
//    }
//  }
  /*-------------------------------------------------------------------------------------------------*/

  // initialize chromosome (from known parameter values)
  template <typename T> inline void Chromosome< T >::initialize()
  {
    chr.clear();

    int i(0);
    for (const auto &x : ptr->param)
    {
      // encoding parameter initial value
      std::string str = x->encode(ptr->initialSet[i++]);
      chr.append(str);

      //_sigma[i] = 0.0;
      //_sigma_iteration[i] = 0;
    }
  }

  /*-------------------------------------------------------------------------------------------------*/

  // evaluate chromosome fitness
  template <typename T> inline void Chromosome< T >::evaluate()
  {
    int i(0);
    for (const auto &x : ptr->param)
    {
      // decoding chromosome: converting chromosome string into a real value
      param[i] = x->decode(chr.substr(ptr->idx[i], x->size()));
      std::cout << " param[" << i << "]: " << param[i];
      i++;
    }

    // computing objective result(s)
    result = ptr->Objective(param);

    // computing sum of all results (in case there is not only one objective functions)
    total = std::accumulate(result.begin(), result.end(), 0.0);

    // initializing fitness to this total
    fitness = total;
    std::cout << " fitness: " << fitness << std::endl;

    std::ofstream outvalue;
    outvalue.open("../value.txt", std::ios::app);
    outvalue << std::fixed << fitness << std::endl;
  }

  /*-------------------------------------------------------------------------------------------------*/
  // evaluate chromosome fitness for 0 generations
  template <typename T>
  inline void Chromosome<T>::evaluate0gen(Eigen::VectorXd observation)
  {
    /// removed passing the value to param, with clustering pop as instead
    // computing objective result(s) std::vector< double > result;
    //result = ptr->Objective(param); //std::vector<double> Objective
    std::vector<double> vec(observation.data(), observation.data() + observation.size());
    result.push_back(vec[0]);
    // computing sum of all results (in case there is not only one objective functions)
    total = result[0]; //std::accumulate(result.begin(), result.end(), 0.0); double total

    // initializing fitness to this total
    fitness = total; //double fitness
//    std::cout << "result[0]: " << result[0]
//              << " total: " << total
//              << " fitness: " << fitness << std::endl;
//
//    std::ofstream outvalue;
//    outvalue.open("../value.txt", std::ios::app);
//    outvalue << std::fixed << fitness << std::endl;
  }
  /*-------------------------------------------------------------------------------------------------*/
  // get the number of generations
  template <typename T>
  inline int Chromosome<T>::get_ga_nogen() const
  {
    return ptr->nogen;
  }

  /*-------------------------------------------------------------------------------------------------*/

  // reset chromosome
  template <typename T> inline void Chromosome< T >::reset()
  {
    chr.clear();
    result = 0.0;
    total = 0.0;
    fitness = 0.0;
  }

  /*-------------------------------------------------------------------------------------------------*/

  // set or replace kth gene by a new one
  template <typename T> inline void Chromosome< T >::setGene(int k)
  {
#ifndef NDEBUG
    if (k < 0 || k >= ptr->nbparam)
    {
      throw std::invalid_argument(
          "Error: in galgo::Chromosome<T>::setGene(int), argument cannot be outside interval [0,nbparam-1], please amend.");
    }
#endif

    // generating a new gene
    std::string s = ptr->param[k]->encode();

    // adding or replacing gene in chromosome
    chr.replace(ptr->idx[k], s.size(), s, 0, s.size());
  }

  /*-------------------------------------------------------------------------------------------------*/

  // initialize or replace kth gene by a know value
  template <typename T>
  inline void Chromosome< T >::initGene(
      int k,
      T x)
  {
#ifndef NDEBUG
    if (k < 0 || k >= ptr->nbparam)
    {
      throw std::invalid_argument(
          "Error: in galgo::Chromosome<T>::initGene(int), first argument cannot be outside interval [0,nbparam-1], please amend.");
    }
#endif

    // encoding gene
    std::string s = ptr->param[k]->encode(x);

    // adding or replacing gene in chromosome
    chr.replace(ptr->idx[k], s.size(), s, 0, s.size());
  }

  /*-------------------------------------------------------------------------------------------------*/

  // add chromosome bit to chromosome (when constructing a new one)
  template <typename T> inline void Chromosome< T >::addBit(char bit)
  {
    chr.push_back(bit);

#ifndef NDEBUG
    if (chr.size() > chrsize)
    {
      throw std::out_of_range(
          "Error: in galgo::Chromosome<T>::setBit(char), exceeding chromosome size.");
    }
#endif
  }

  /*-------------------------------------------------------------------------------------------------*/

  // initialize or replace an existing chromosome bit
  template <typename T>
  inline void Chromosome< T >::setBit(
      char bit,
      int pos)
  {
#ifndef NDEBUG
    if (pos >= chrsize)
    {
      throw std::out_of_range(
          "Error: in galgo::Chromosome<T>::replaceBit(char, int), second argument cannot be equal or greater than chromosome size.");
    }
#endif

    std::stringstream ss;
    std::string str;
    ss << bit;
    ss >> str;
    chr.replace(pos, 1, str);
    std::cout << chr << "\n";
  }

  /*-------------------------------------------------------------------------------------------------*/

  // flip an existing chromosome bit
  template <typename T> inline void Chromosome< T >::flipBit(int pos)
  {
#ifndef NDEBUG
    if (pos >= chrsize)
    {
      throw std::out_of_range(
          "Error: in galgo::Chromosome<T>::flipBit(int), argument cannot be equal or greater than chromosome size.");
    }
#endif

    if (chr[pos] == '0')
    {
      chr.replace(pos, 1, "1");
    }
    else
    {
      chr.replace(pos, 1, "0");
    }
  }

  /*-------------------------------------------------------------------------------------------------*/

  // get a chromosome bit
  template <typename T> inline char Chromosome< T >::getBit(int pos) const
  {
#ifndef NDEBUG
    if (pos >= chrsize)
    {
      throw std::out_of_range(
          "Error: in galgo::Chromosome<T>::getBit(int), argument cannot be equal or greater than chromosome size.");
    }
#endif

    return chr[pos];
  }

  /*-------------------------------------------------------------------------------------------------*/

  // initialize or replace a portion of bits with a portion of another chromosome (from position start to position end included)
  template <typename T>
  inline void Chromosome< T >::setPortion(
      const Chromosome< T > &x,
      int start,
      int end)
  {
#ifndef NDEBUG
    if (start > chrsize)
    {
      throw std::out_of_range(
          "Error: in galgo::Chromosome<T>::setPortion(const Chromosome<T>&, int, int), second argument cannot be greater than chromosome size.");
    }
#endif
    ///replace chr(strat, end-start+1) with x.chr(start, end-start+1)
    chr.replace(start, end - start + 1, x.chr, start, end - start + 1);
  }

  /*-------------------------------------------------------------------------------------------------*/

  // initialize or replace a portion of bits with a portion of another chromosome (from position start to the end of he chromosome)
  template <typename T>
  inline void Chromosome< T >::setPortion(
      const Chromosome< T > &x,
      int start)
  {
#ifndef NDEBUG
    if (start > chrsize)
    {
      throw std::out_of_range(
          "Error: in galgo::Chromosome<T>::setPortion(const Chromosome<T>&, int), second argument cannot be greater than chromosome size.");
    }
#endif
    ///replace chr(strat, chrsize) with x.chr(start, x.chrsize)
    chr.replace(start, chrsize, x.chr, start, x.chrsize);
  }

  /*-------------------------------------------------------------------------------------------------*/

  // get parameter value(s) from chromosome
  template <typename T>
  inline const std::vector< T > &Chromosome< T >::getParam() const
  {
    return param;
  }

  /*-------------------------------------------------------------------------------------------------*/

  // get objective function result
  template <typename T>
  inline const std::vector< double > &Chromosome< T >::getResult() const
  {
    return result;
  }

  /*-------------------------------------------------------------------------------------------------*/

  // get the total sum of all objective function(s) result
  template <typename T> inline double Chromosome< T >::getTotal() const
  {
    return total;
  }

  /*-------------------------------------------------------------------------------------------------*/

  // get constraint value(s) for this chromosome
  template <typename T>
  inline const std::vector< double > Chromosome< T >::getConstraint() const
  {
    return ptr->Constraint(param);
  }

  /*-------------------------------------------------------------------------------------------------*/

  // return chromosome size in number of bits
  template <typename T> inline int Chromosome< T >::size() const
  {
    return chrsize;
  }

  /*-------------------------------------------------------------------------------------------------*/

  // return mutation rate
  template <typename T> inline double Chromosome< T >::mutrate() const
  {
    return ptr->mutrate;
  }

  template <typename T>
  inline double Chromosome< T >::recombination_ratio() const
  {
    return ptr->recombination_ratio;
  }

  template <typename T>
  inline const MutationInfo <T> &Chromosome< T >::mutinfo() const
  {
    return ptr->mutinfo;
  }


  /*-------------------------------------------------------------------------------------------------*/

  // return number of genes in chromosome
  template <typename T> inline int Chromosome< T >::nbgene() const
  {
    return ptr->nbparam;
  }

  /*-------------------------------------------------------------------------------------------------*/

  // return numero of generation this chromosome belongs to
  template <typename T> inline int Chromosome< T >::nogen() const
  {
    return numgen;
  }

  /*-------------------------------------------------------------------------------------------------*/

  // return lower bound(s)
  template <typename T>
  inline const std::vector< T > &Chromosome< T >::lowerBound() const
  {
    return ptr->lowerBound;
  }

  /*-------------------------------------------------------------------------------------------------*/

  // return upper bound(s)
  template <typename T>
  inline const std::vector< T > &Chromosome< T >::upperBound() const
  {
    return ptr->upperBound;
  }


  template <typename T> T Chromosome< T >::get_value(int k) const
  {
#ifndef NDEBUG
    if (k < 0 || k >= ptr->nbparam)
    {
      throw std::invalid_argument(
          "Error: in galgo::Chromosome<T>::get_value(int), first argument cannot be outside interval [0,nbparam-1], please amend.");
    }
#endif

    auto &x = ptr->param[k];
    return x->decode(chr.substr(ptr->idx[k], x->size()));
  }


  template <typename T> double Chromosome< T >::get_sigma(int k) const
  {
    return _sigma[k];
  }

  template <typename T> long Chromosome< T >::get_sigma_iteration(int k) const
  {
    return _sigma_iteration[k];
  }
  //=================================================================================================

}

#endif
