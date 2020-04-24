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
* Description: Position based (servo) motor
* Author: Elte Hupkes
*
*/


#include <string>
#include "iostream"

#include "torch/torch.h"

class InverseNetworkImpl : public torch::nn::Module {
    /// \brief Constructor
public: explicit InverseNetworkImpl(
            int actuatorsize
    );

    /// \brief Destructor
public: ~InverseNetworkImpl() override;

    /// \brief Forward function
public: torch::Tensor forward(torch::Tensor x);

private:
    /// \brief Layers
    torch::nn::Linear linear_In, linear_H1, linear_Out;

    /// \brief Biases
    torch::Tensor bias_in, bias_h1, bias_out;

};

TORCH_MODULE(InverseNetwork);