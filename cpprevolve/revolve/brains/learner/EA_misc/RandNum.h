#pragma once
#ifndef RANDNUM_H
#define RANDNUM_H

#include <memory>
#include <random>
#include <Eigen/Core>

namespace revolve {

class RandNum
{
public:
    typedef std::shared_ptr<RandNum> Ptr;
    typedef std::shared_ptr<const RandNum> ConstPtr;

	explicit RandNum(int seed); // instantiate the class and specify the initial seed.
	~RandNum();

    /**
     * @brief random number between a lower bound and a upper bound included
     * @param lower bound (double)
     * @param upper bound (double)
     * @return a double
     */
	double randDouble(double lower, double upper); // creates a random float between two specified values.

    /**
     * @brief random number between a lower bound and a upper bound included
     * @param lower bound (float)
     * @param upper bound (float)
     * @return a float
     */
    float randFloat(float lower, float upper); // creates a random float between two specified values.

    /**
     * @brief random number between a lower bound and a upper bound included
     * @param lower bound (int)
     * @param upper bound (int)
     * @return an integer
     */
    int randInt(int lower, int upper); // creates a random integer (range, offset)

    /**
     * @brief Generate a random vector of double
     * @param lower bound
     * @param upper bound (included
     * @param size of the vector
     * @return
     */
    std::vector<double> randVectd(double lower, double upper, int size);

    /**
     * @brief Generate a random number from a normal distribution
     * @param mean of the distribution
     * @param variance of the distribution
     * @return
     */
    double normalDist(double mu, double sigma);

    void setSeed(int seed); // sets the seed of the random number generator
	int m_seed = 0;
	int getSeed();
    std::mt19937 gen;

    Eigen::ArrayXXi Bernoulli(double p, const int *len);
};

}//EA_misc

#endif //RANDNUM_H
