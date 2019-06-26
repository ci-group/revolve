/*
 * Copyright (C) 2015-2018 Vrije Universiteit Amsterdam
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
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
 * Date: December 29, 2018
 *
 */

#ifndef REVOLVE_DIFFERENTIALCPG_H_
#define REVOLVE_DIFFERENTIALCPG_H_

#include <map>
#include <tuple>

#include "Brain.h"

namespace revolve
{
  namespace gazebo
  {
    class DifferentialCPG
        : public Brain
    {
      /// \brief Constructor
      /// \param[in] _modelName Name of the robot
      /// \param[in] _node The brain node
      /// \param[in] _motors Reference to a motor list, it be reordered
      /// \param[in] _sensors Reference to a sensor list, it might be reordered
      public: DifferentialCPG(
          const ::gazebo::physics::ModelPtr &_model,
          const sdf::ElementPtr _settings,
          const std::vector< MotorPtr > &_motors,
          const std::vector< SensorPtr > &_sensors);

      /// \brief Destructor
      public: virtual ~DifferentialCPG();

      /// \brief The default update method for the controller
      /// \param[in] _motors Motor list
      /// \param[in] _sensors Sensor list
      /// \param[in] _time Current world time
      /// \param[in] _step Current time step
      public: virtual void Update(
          const std::vector< MotorPtr > &_motors,
          const std::vector< SensorPtr > &_sensors,
          const double _time,
          const double _step);

      protected: void Step(
          const double _time,
          double *_output);

      /// \brief Register of motor IDs and their x,y-coordinates
      protected: std::map< std::string, std::tuple< int, int > >
          positions_;

      /// \brief Register of individual neurons in x,y,z-coordinates
      /// \details x,y-coordinates define position of a robot's module and
      // z-coordinate define A or B neuron (z=1 or -1 respectively). Stored
      // values are a bias and a gain of each neuron.
      protected: std::map< std::tuple< int, int, int >,
                           std::tuple< double, double, double > > neurons_;

      /// \brief Register of connections between neighnouring neurons
      /// \details Coordinate set of two neurons (x1, y1, z1) and (x2, y2, z2)
      // define a connection.
      protected: std::map< std::tuple< int, int, int, int, int, int >,
                           double > connections_;

      /// \brief Used to determine the next state array
      private: double *nextState_;

      /// \brief One input state for each input neuron
      private: double *input_;

      /// \brief Used to determine the output to the motors array
      private: double *output_;
    };
  }
}

#endif //REVOLVE_DIFFERENTIALCPG_H_
