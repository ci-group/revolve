/*
* Copyright (C) 2017 Vrije Universiteit Amsterdam
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
* Author: Gongjin Lan
* Date: November 07, 2018
*
*/

#ifndef REVOLVE_GAZEBO_BRAIN__NEURON_H_
#define REVOLVE_GAZEBO_BRAIN__NEURON_H_

#include <vector>

namespace revolve
{
  namespace gazebo
  {
    class Neuron
    {
      /// \brief Constructor
      public: explicit Neuron() {}

      /// \brief Destructor
      public: virtual ~Neuron() {}

      /// \brief Update the situation of a neuron.
      /// \param[in] _weights List of weights
      /// \param[in] _bias double bias
      /// \param[out] _output the output of a neuron
      public: virtual void Update(
          const std::vector<double> &_inputs,
          const double _bias) = 0;

      /// \brief Output the value from activation function
      /// \return Output of the neuron
      public: virtual double Output();
    };
  } /* namespace gazebo */
} /* namespace revolve */

#endif  // REVOLVE_GAZEBO_BRAIN__NEURON_H_
