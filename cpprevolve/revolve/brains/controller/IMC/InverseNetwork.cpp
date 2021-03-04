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
* Author: Fuda van Diggelen
*
*/

#include "torch/torch.h"
#include "InverseNetwork.h"


/////////////////////////////////////////////////
InverseNetworkImpl::InverseNetworkImpl(
        int actuatorsize)
        :   linear_In(actuatorsize * 4, actuatorsize * 4),
            linear_H1(actuatorsize * 4, actuatorsize * 4),
            linear_Out( actuatorsize* 4,actuatorsize)
{
    // register_module() is needed if we want to use the parameters() method later on
    register_module("linear_In", linear_In);
    register_module("linear_H1", linear_H1);
    register_module("linear_Out", linear_Out);

    bias_in = register_parameter("bias_in", torch::randn(actuatorsize * 4));
    bias_h1 = register_parameter("bias_h1", torch::randn(actuatorsize * 4));
    bias_out = register_parameter("bias_out", torch::randn(actuatorsize));
}


torch::Tensor InverseNetworkImpl::forward(torch::Tensor x){
    x = torch::relu(linear_In->forward(x)+bias_in);
    x = torch::relu(linear_H1->forward(x)+bias_h1);
    x = torch::tanh(linear_Out->forward(x)+bias_out);
    return x;
}

InverseNetworkImpl::~InverseNetworkImpl() = default;

