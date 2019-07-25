/*
* Copyright (C) 2017 Vr˝ıje Universiteit Amsterdam
*
* Licensed under the Apache License, Version 2.0 (the "License");
* You may obtain a copy of the License at
*
*     http://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
*
* Description: TODO: <Add brief description about file purpose>
* Author: Milan Jelisavcic
* Date: March 28, 2016
*
*/

#ifndef REVOLVE_GAZEBO_BRAIN_RLPOWER_H_
#define REVOLVE_GAZEBO_BRAIN_RLPOWER_H_

#include <cmath>
#include <functional>
#include <map>
#include <string>
#include <vector>

#include <boost/thread/mutex.hpp>
#include <gazebo/gazebo.hh>

#include <revolve/msgs/spline_policy.pb.h>

#include "Evaluator.h"
#include "Brain.h"

namespace revolve
{
  namespace gazebo
  {
    class RLPower
            : public Brain
    {
      typedef const std::shared_ptr<revolve::msgs::ModifyPolicy const>
          ConstModifyPolicyPtr;

      static const size_t MAX_EVALUATIONS;
      static const size_t MAX_RANKED_POLICIES;
      static const size_t INTERPOLATION_CACHE_SIZE;
      static const size_t INITIAL_SPLINE_SIZE;
      static const size_t UPDATE_STEP;
      static const double EVALUATION_RATE;
      static const double SIGMA_START_VALUE;
      static const double SIGMA_TAU_CORRECTION;

      /// \brief The default number of update points in a spline cycle
      static const double CYCLE_LENGTH;

      /// \brief The constant for defining the random distribution
      static const double SIGMA;

      /// \brief The RLPower constructor reads out configuration file,
      /// deretmines which algorithm type to apply and initialises new policy.
      /// \param[in] _modelName: name of a robot
      /// \param[in] _node: configuration file
      /// \param[in] _motors: vector list of robot's actuators
      /// \param[in] _sensors: vector list of robot's sensors
      /// \return pointer to the RLPower class object
      public: RLPower(
          const ::gazebo::physics::ModelPtr &_model,
          const sdf::ElementPtr &_settings,
          const std::vector< MotorPtr > &_motors,
          const std::vector< SensorPtr > &_sensors);

      /// \brief Destructor
      public: ~RLPower() override;

      /// \brief  Method for updating sensors readings, actuators positions,
      /// ranked list of policies and generating new policy
      /// \param[in] _motors: vector list of robot's actuators
      /// \param[in] _sensors: vector list of robot's sensors
      /// \param[in] _time:
      /// \param[in] _step:
      public: void Update(
          const std::vector< MotorPtr > &_motors,
          const std::vector< SensorPtr > &_sensors,
          double _time,
          double _step) override;

      /// \brief
      protected: struct Config;

      /// \brief Static method to parse received configuration file
      public: static Config ParseSDF(const sdf::ElementPtr &_brain);

      /// \brief Steps through the splines
      protected: void Step(const double _time);

      /// \brief
      protected: struct Config
      {
        std::string algorithmType;
        size_t evaluationRate;
        size_t interpolationSplineSize;
        size_t nEvaluations;
        size_t maxRankedPolicies;
        double sigma;
        double tau;
        size_t sourceYSize;
        size_t updateStep;
        std::string policyLoadPath;
      };

      /// \brief Request handler to modify the neural network
      protected: void Modify(ConstModifyPolicyPtr &_request);

      /// \brief Mutex for stepping / updating the network
      protected: boost::mutex rlpowerMutex_;

      /// \brief Network modification subscriber
      protected: ::gazebo::transport::SubscriberPtr alterSub_;

      /// \brief Generate new policy
      private: void InitialisePolicy(size_t _numSplines);

      /// \brief Evaluate the current policy and generate new
      private: void UpdatePolicy(const size_t _numSplines);

      /// \brief  Load saved policy from JSON file
      private: void LoadPolicy(const std::string &_policyPath);

      /// \brief Generate interpolated spline based on number of sampled control
      /// points in 'source_y'
      /// \param[in] _sourceY: set of control points over which interpolation is
      /// generated
      /// \param[out] _destinationY: set of interpolated control points
      /// (default 100)
      private: void InterpolateCubic(
          const size_t _numSplines,
          Policy *const _sourceY,
          Policy *_destinationY);

      /// \brief Increment number of sampling points for policy
      private: void IncreaseSplinePoints(const size_t _numSplines);

      /// \brief Randomly select two policies and return the one with higher
      /// fitness
      /// \return an iterator from 'ranked_policies_' map
      private: std::map< double, PolicyPtr >::iterator BinarySelection();

      /// \brief Extracts the value of the current_policy in x=time using linear
      /// interpolation
      /// Writes the output in output_vector
      private: void Output(
          const size_t _numSplines,
          const double _time,
          double *_output);

      /// \brief Retrieves fitness for the current policy
      /// \return
      private: double Fitness();

      /// \brief Writes current spline to file
      private: void LogCurrentSpline();

      /// \brief Writes best 10 splines to file
      private: void LogBestSplines();

      /// \brief Pointer to the current policy
      private: PolicyPtr currentPolicy_ = NULL;

      /// \brief Pointer to the interpolated current_policy_ (default 100)
      private: PolicyPtr interpolationCache_ = NULL;

      /// \brief Pointer to the fitness evaluator
      private: EvaluatorPtr evaluator_ = NULL;

      /// \brief Number of current generation
      private: size_t generationCounter_;

      /// \brief Number of 'interpolation_cache_' sample points
      private: size_t numInterpolationPoints_;

      /// \brief Maximal number of stored ranked policies
      private: size_t maxRankedPolicies_;

      /// \brief Maximal numberEvaluator of evaluations
      private: size_t maxEvaluations_;

      /// \brief The size of a spline before beeing increased
      private: size_t sourceYSize_;

      /// \brief
      private: size_t stepRate_;

      /// \brief Number of evaluations after which sampling size increases
      private: size_t updateStep_;

      /// \brief Cycle start time
      private: double cycleStartTime_;

      /// \brief Evaluation rate
      private: double evaluationRate_;

      /// \brief Noise in generatePolicy() function
      private: double sigma_;

      /// \brief Tau deviation for self-adaptive sigma
      private: double tau_;

      /// \brief
      private: double startTime_;

      /// \brief Name of the robot
      private: ::gazebo::physics::ModelPtr robot_;

      /// \brief Type of the used algorithm
      private: std::string algorithmType_;

      /// \brief Load path for previously saved policies
      private: std::string policyLoadPath_;

      /// \brief Container for best ranked policies
      private: std::map< double, PolicyPtr, std::greater< double>>
          rankedPolicies_;
    };
  }
}

#endif  // REVOLVE_GAZEBO_BRAIN_RLPOWER_H_
