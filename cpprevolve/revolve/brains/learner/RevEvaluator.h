//
// Created by andi on 27-11-19.
//

#ifndef REVOLVE_EVALUATOR_H
#define REVOLVE_EVALUATOR_H

#endif //REVOLVE_EVALUATOR_H
namespace revolve
{
        class RevEvaluator
        {
            /// \brief Constructor
        public: RevEvaluator(const double _evaluationRate,
                             const double step_saving_rate = 0.1)
            : step_saving_rate(step_saving_rate)
            , evaluation_rate(_evaluationRate){};

            /// \brief Destructor
        public: ~RevEvaluator();

            /// \brief Initialisation method
        public: void Reset();

            /// \brief Retrieve the fitness
            /// \return A fitness value according to a given formula
        public: double Fitness();

            /// brief Specifies locomotion type
        public: std::string locomotion_type;

            /// \brief Update the position
            /// \param[in] _pose Current position of a robot
        /*public: void Update(const ignition::math::Pose3d &_pose,
                            const double time,
                            const double step);*/

            /// \brief
        protected: double evaluation_rate;

        protected: double path_length = 0.0;

        protected: double last_step_time;
        protected: double step_saving_rate;
        public: std::string directory_name = "";
        };
    }