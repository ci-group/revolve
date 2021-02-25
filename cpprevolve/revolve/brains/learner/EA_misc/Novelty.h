//
// Created by fuda on 12/7/20.
//

#ifndef REVOLVE_NOVELTY_H
#define REVOLVE_NOVELTY_H

#include "../EA.h"
#include <tbb/tbb.h>
#include <Eigen/Core>
#include "RandNum.h"

namespace revolve {

    struct Novelty {

        /**
         * @brief compute sparseness from a given list of distances and k_value a static parameter
         * @param a sorted list of distances.
         * @return sparseness
         */
        static double sparseness(const std::vector<double> &dist);

        /**
         * @brief add ind to the archive if its novelty score is above a threshold or according a certain probability
         * @param individual
         * @param novelty score of the individual
         * @param archive
         * @param seed for the add archive probability
         */
        static void update_archive(const Eigen::VectorXd& ind_desc,
                                   double ind_nov,
                                   std::vector<Eigen::VectorXd> &archive,
                                   const RandNum::Ptr &rn);


        /**
         * @brief Compute distances of a descriptor to the archive and a population. And return the vector of distances sorted in increasing order.
         * @param descriptor
         * @param archive of descriptor
         * @param population
         * @return vector of distances
         */
        static std::vector<double> distances(const Eigen::VectorXd& desc,
                                             const std::vector<Eigen::VectorXd> &archive,
                                             const std::vector<Eigen::VectorXd> &pop);

        /**
         * @brief Compute distances of a descriptor to the archive and a population. And return the vector of distances sorted in increasing order.
         * @param descriptor
         * @param archive of descriptor
         * @param population
         * @param output : sorted indexes of the population from the closest to the farthest of the desc
         * @return vector of distances
         */
        static std::vector<double> distances(const Eigen::VectorXd& desc,
                                             const std::vector<Eigen::VectorXd> &archive,
                                             const std::vector<Eigen::VectorXd> &pop,
                                             std::vector<size_t> & sorted_pop_indexes);


        static int k_value;
        static double novelty_thr;
        static double archive_adding_prob;
    };
}

#endif //REVOLVE_NOVELTY_H
