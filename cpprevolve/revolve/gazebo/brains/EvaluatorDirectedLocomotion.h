//
// Created by Gongjin Lan on 4/17/19.
//

#ifndef REVOLVE_EVALUATORDIRECTEDLOCOMOTION_H
#define REVOLVE_EVALUATORDIRECTEDLOCOMOTION_H

#include "Evaluator.h"

namespace revolve
{
  namespace gazebo
  {
    class EvaluatorDirectedLocomotion
        : public Evaluator
    {
      public: EvaluatorDirectedLocomotion(
          const double _evaluationRate,
          const double step_saving_rate = 0.1);

      public: virtual ~EvaluatorDirectedLocomotion();

      public: virtual void Reset(double Time) override;

      public: virtual double Fitness() override;

      public: virtual void Update(const ignition::math::Pose3d &_pose,
                                  const double time,
                                  const double step) override;

      protected: double last_step_time;
      protected: double step_saving_rate;
      protected: std::vector<ignition::math::Pose3d> step_poses;

      private: double distP2P = 0.0;
      private: double lengthPath = 0.0;
    };
  }
}


#endif //REVOLVE_EVALUATORDIRECTEDLOCOMOTION_H
