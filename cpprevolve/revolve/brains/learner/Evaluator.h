//
// Created by andi on 27-11-19.
//

#ifndef REVOLVE_EVALUATOR_H
#define REVOLVE_EVALUATOR_H

namespace revolve {
class Evaluator
{
    /// \brief Constructor
public:
    Evaluator() = default;

    /// \brief Destructor
    virtual ~Evaluator() = default;

    /// \brief Initialisation method
    virtual void reset() = 0;

    /// \brief Retrieve the fitness
    /// \return A fitness value according to a given formula
    virtual double fitness() = 0;

    /// \brief Update the position
    /// \param[in] _pose Current position of a robot
    //virtual void update(const ignition::math::Pose3d &_pose,
    //                    const double time,
    //                    const double step) = 0;
};
}

#endif //REVOLVE_EVALUATOR_H