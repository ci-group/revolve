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
#include "FeedForwardNetwork.h"


/////////////////////////////////////////////////
FeedForwardNetworkImpl::FeedForwardNetworkImpl(
        int actuatorsize)
        :   linear_In(actuatorsize * 3, actuatorsize * 3),
            linear_H1(actuatorsize * 3, actuatorsize * 3),
            linear_Out(actuatorsize * 3,actuatorsize* 2)
{
    // register_module() is needed if we want to use the parameters() method later on
    register_module("linear_In", linear_In);
    register_module("linear_H1", linear_H1);
    register_module("linear_Out", linear_Out);

    bias_in = register_parameter("bias_in", torch::randn(actuatorsize * 3));
    bias_h1 = register_parameter("bias_h1", torch::randn(actuatorsize * 3));
    bias_out = register_parameter("bias_out", torch::randn(actuatorsize * 2));
}


torch::Tensor FeedForwardNetworkImpl::forward(torch::Tensor x){
    x = torch::relu(linear_In->forward(x)+bias_in);
    x = torch::relu(linear_H1->forward(x)+bias_h1);
    x = torch::tanh(linear_Out->forward(x)+bias_out);
    return x;
}

FeedForwardNetworkImpl::~FeedForwardNetworkImpl() = default;

