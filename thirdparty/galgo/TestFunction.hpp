//=================================================================================================
//                  Copyright (C) 2018 Alain Lanthier - All Rights Reserved  
//                  License: MIT License    See LICENSE.md for the full license.
//                  Original code 2017 Olivier Mallet (MIT License)              
//=================================================================================================

#ifndef TESTFUNCTION_HPP
#define TESTFUNCTION_HPP

/********** 1# ACKLEY function N Dimensions **************/
template <typename T>
class AckleyObjective
{
  public:
  static std::vector<double> Objective(const std::vector<T>& x)
  {
    size_t dim_in = 5;
    auto xx = x;
    // transfer interval from [0, 1] to [-32.768, 32.768]
    for (int i = 0; i < dim_in; i++)
    {
      xx[i] = 65.536 * x[i] - 32.768;
    }
    const double a = 20.;
    const double b = 0.2;
    const double c = 2 * M_PI;
    double sum1 = 0.;
    double sum2 = 0.;
    for (size_t i = 0; i < dim_in; i++)
    {
      sum1 = sum1 + xx[i] * xx[i];
      sum2 = sum2 + std::cos(c * xx[i]);
    }
    double term1 = -a * std::exp(-b * std::sqrt(sum1 / dim_in));
    double term2 = -std::exp(sum2 / dim_in);
    double obj = term1 + term2 + a + std::exp(1);
    return {-obj}; //max = 0, at (0,...,0)
  }
};

/********** 2# SCHWEFEL function N Dimensions **************/
template <typename T>
class SchwefelObjective //todo not accurate results
{
  public:
  static std::vector<double> Objective(const std::vector<T>& x)
  {
    size_t dim_in = 20;
    auto xx = x;
    //transfer [0, 1] to [-500, 500] [250, 500] [100,500] [200,500]
    for (int i = 0; i < dim_in; i++)
    {
      xx[i] = 300. * x[i] + 200.;
    }
    double sum = 0.;
    for (size_t i = 0; i < dim_in; i++)
    {
      sum = sum + xx[i] * sin(sqrt(abs(xx[i])));
    }
    double obj = 418.9829 * dim_in - sum;//X1 = 0.9209721088 | X2 = 0.9209100604 | F(x) = -0.0004374512
    return {-obj}; //maximum = 0 with (420.9687, ..., 420.9687)
  }
};

/********** 3# Ellipsoid function N Dimensions **************/
template <typename T>
class EllipsoidObjective
{
  public:
  static std::vector<double> Objective(const std::vector<T>& x)
  {
    size_t dim_in = 5;
    double inner = 0., outer = 0.;
    for (size_t i = 0; i < dim_in; ++i)
    {
        for(size_t j = 0; j < i; j++)
        {
            inner = inner + std::pow((131.072 * x[j] - 65.536), 2); //(-65.536, 65.536)
        }
        outer = outer + inner;
    }
    return {-outer}; //maximum = 0 at (0, ..., 0)
  }
};

/********** 4# Sphere function N Dimensions **************/
template <typename T>
class SphereObjective
{
  public:
  static std::vector<double> Objective(const std::vector<T>& x)
  {
    size_t dim_in = 5;
    double inner = 0.;
    for (size_t i = 0; i < dim_in; ++i)
    {
        inner = inner + std::pow((10. * x[i] - 5.), 2);
    }
    return {-inner}; //maximum = 0 with (0, 0)
  }
};

/********** 5# Rosenbrock  function N Dimensions **************/
template <typename T>
class RosenbrockObjective //todo not good results
{
  public:
  static std::vector<double> Objective(const std::vector<T>& x)
  {
    size_t dim_in = 5;
    auto xx = x;
    // transfer interval from [0, 1] to [-5, 10]
    for (int i = 0; i < dim_in; i++)
        xx[i] = 15. * x[i] - 5.;
    double sum = 0.;
    double term = 0.;
    double xnext = 0.;
    for(size_t i = 0; i < (dim_in - 1); i++)
    {
        xnext = xx[i + 1];
        term = 100. * std::pow((xnext - xx[i] * xx[i]), 2.0) + std::pow((xx[i] - 1), 2.0);
        sum = sum + term;
    }
    double obj = sum;
    return {-obj}; //maximum = 0 with (1,...,1)
  }
};

/********* 6# Michalewicz function N = 2/5/10 Dimensions **********/
template <typename T>
class MichalewiczObjective //todo not good results
{
  public:
  static std::vector<double> Objective(const std::vector<T>& x)
  {
    size_t dim_in = 5;
    auto xx = x;
    // transfer interval from [0, 1] to [0, pi]
    for (int i = 0; i < dim_in; i++)
        xx[i] = M_PI * x[i];
    double sum = 0.;
    double term = 0.;
    double m = 10.;
    for(size_t i = 0; i < dim_in; i++)
    {
        term = std::sin(xx[i]) * std::pow(std::sin(i * xx[i] * xx[i]/M_PI), 2 * m);
        sum = sum + term;
    }
    double obj = sum;
    return {obj}; //max= -1.8013(2D) at (2.20,1.57)/-4.687658(5D)/-9.66015(10D)
  }
};

/********** 7# StyblinskiTang function N Dimensions ****************/
template <typename T>
class StyblinskiTangObjective
{
  public:
  static std::vector<double> Objective(const std::vector<T>& x)
  {
    size_t dim_in = 20;
    auto xx = x;
    // transfer interval from [0, 1] to [-5, 5] [-4,4]
    for (int i = 0; i < dim_in; i++)
      xx[i] = 10. * x[i] - 5.;
    double sum = 0.;
    double term;
    for(size_t i = 0; i < dim_in; i++)
    {
      term = std::pow(xx[i], 4.0) - 16 * xx[i] * xx[i] + 5 * xx[i];
      sum = sum + term;
    }
    double obj = sum/2.0;
    return {-obj}; //max= 39.16599 * d, (5D:195.82995)at (-2.903534,...,-2.903534)
  }
};

/********** Rastrigin function N Dimensions ****************/
template <typename T>
class RastriginObjective
{
  public:
  static std::vector<double> Objective(const std::vector<T>& x)
  {
    size_t dim_in = 20;
    auto xx = x;
    //transfer interval from [0, 1] to [-3, 3] [-2, 2] [-5, 5]
    for (int i = 0; i < dim_in; i++)
      xx[i] = 4. * x[i] - 2.;
    double f = 10. * dim_in;
    for (size_t i = 0; i < dim_in; ++i)
      f += xx[i] * xx[i] - 10. * std::cos(2 * M_PI * xx[i]);
    return {-f}; //maximum = 0 with (0, 0, 0, 0);
  }
};

/********** Griewank function N Dimensions ****************/
template <typename T>
class GriewankObjective
{
  public:
  static std::vector<double> Objective(const std::vector<T>& x)
  {
    size_t dim_in = 20;
    auto xx = x;
    //transfer interval from [0, 1] to [-10, 10] or [-5, 5] [-6,6]
    for (int i = 0; i < dim_in; i++)
      xx[i] = 10. * x[i] - 5.;
    double sum = 0.0, f = 1.0;
    for (size_t i = 0; i < dim_in; ++i)
    {
      sum += xx[i] * xx[i]/4000;
      f = f * std::cos(xx[i]/std::sqrt(i+1));
    }
    double obj = sum - f + 1;
    return {-obj}; //maximum = 0 with (0, 0, 0, 0);
  }
};


/********** 8# Powell function N >= 4 Dimensions *************/
template <typename T>
class PowellObjective //todo not good results
{
  public:
  static std::vector<double> Objective(const std::vector<T>& x)
  {
    size_t dim_in = 5;
    auto xx = x;
    // transfer interval from [0, 1] to [-4, 5]
    for (int i = 0; i < dim_in; i++)
        xx[i] = 9 * x[i] - 4;
    double sum = 0.;
    double term1, term2, term3, term4;
    for(size_t i = 0; i < dim_in/4; i++)
    {
      term1 = std::pow((xx[4 * i - 3] + 10 * xx[4 * i - 2]), 2.0);
      term2 = 5 * std::pow((xx[4 * i - 1] - xx[4 * i]), 2.0);
      term3 = std::pow(xx[4 * i - 2] - 2 * xx[4 * i - 1], 4.0);
      term4 = 10 * std::pow(xx[4 * i - 3] - xx[4 * i], 4.0);
      sum = sum + term1 + term2 + term3 + term4;
      std::cout << std::endl << "i: " << i
                << " sum: " << sum << " term1: " << term1 << " term2: " << term2
                << " term3: " << term3 << " term4: " << term4 << std::endl;
    }
    double obj = sum;
    return {-obj}; //max= 0 at (0,...,0)
  }
};

//// constraints example:
//template <typename T>
//std::vector<double> MyConstraint(const std::vector<T>& x)
//{
//    double x0 = (double)x[0];
//    double x1 = (double)x[1];
//    return
//    {
//       //x[0]*x[1]+x[0]-x[1]+1.5,   // 1) x * y + x - y + 1.5 <= 0
//       //10-x[0]*x[1]               // 2) 10 - x * y <= 0
//       x0 - 2,    // x0 <= 2
//       x1 - 2     // x1 <= 2
//    };
//}

/*Rastrigin Function*/
template <typename T>
double pso_rastrigin(std::vector< T > particle)
{
    double result(10. * static_cast<T> (particle.size())), A(10.), PI(3.14159);
    for (auto dim : particle) {
        result += pow(dim, 2.) - (A * cos(2. * PI * dim));
    }
    return (result);
}

template <typename T>
class rastriginObjective
{
public:
    static std::vector<double> Objective(const std::vector<T>& x)
    {
        std::vector<double> xd(x.size());
        for (size_t i = 0; i < x.size(); i++) xd[i] = (double)x[i];

        double obj = -pso_rastrigin<double>(xd);
        return { obj };
    }
};

/*
Griewank Function
*/
template <typename T>
double pso_griewank(std::vector< T > particle) 
{
    double sum(0.), product(1.);
    for (int i = 0; i < particle.size(); i++) {
        sum += pow(particle[i], 2.);
        product *= cos(particle[i] / sqrt(i + 1));
    }
    return (1. + (sum / 4000.) - product);
}

//template <typename T>
//class GriewankObjective
//{
//public:
//    static std::vector<double> Objective(const std::vector<T>& x)
//    {
//        std::vector<double> xd(x.size());
//        for (size_t i = 0; i < x.size(); i++) xd[i] = (double)x[i];
//
//        double obj = -pso_griewank<double>(xd);
//        return { obj };
//    }
//};

/*
Styblinski-Tang Function
Min = (-2.903534,...,--2.903534)
*/
template <typename T>
double pso_styb_tang(std::vector< T > particle)
{
    double result(0.);
    for (auto dim : particle) {
        result += pow(dim, 4.0) - (16. * pow(dim, 2.)) + (5. * dim);
    }
    return (result / 2.);
}


template <typename T>
class SumSameAsPrdObjective
{
public:
    static std::vector<double> Objective(const std::vector<T>& x)
    {
        double x0 = (double)x[0];
        double x1 = (double)x[1];

        int ix = (int)x0;
        int iy = (int)x1;
        double sum = ix + iy;
        double prd = ix * iy;
        double diff  = std::fabs(sum - prd);

        double err = 1000 * diff * diff;;
        err += (100 * std::fabs(x0 - ix)* std::fabs(x0 - ix) + 100 * std::fabs(x1 - iy)* std::fabs(x1 - iy));

        double obj = -(diff + err);
        return { obj };
    }
};


#endif