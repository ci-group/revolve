//
// Created by fuda on 16-03-20.
//

//
// Created by fuda on 25-02-20.
//
#include "FeedForwardNetwork.h"
#include "InverseNetwork.h"
#include "torch/torch.h"

#include <iostream>


const std::string NetworkFor = "/home/fuda/Projects/revolve/experiments/examples/output/testFor.log";
const std::string NetworkInv = "/home/fuda/Projects/revolve/experiments/examples/output/testInv.log";
int actuatorsize = 2;
double phase =0.3;
double freq = 2*3.141592654/75;


FeedForwardNetwork FeedForNet(actuatorsize);
torch::optim::Adam FeedFor_Optim(FeedForNet.parameters(),
                                 torch::optim::AdamOptions(3e-2).beta1(0.0).weight_decay(0.001));


InverseNetwork InvNet(actuatorsize);
torch::optim::Adam Inv_Optim(InvNet.parameters(),
                             torch::optim::AdamOptions(3e-2).beta1(0.0).weight_decay(0.001));



torch::Tensor Reference_state_Prev = torch::ones((0,actuatorsize*2)).to(torch::kFloat64)*.5;
torch::Tensor Predicted_state_Prev =Reference_state_Prev.requires_grad_(true);


torch::Tensor InvModel(const torch::Tensor& Current_State,
                       const torch::Tensor& Reference_State,
                       const torch::Tensor& error
){
    torch::Tensor Network_Input_Inv = torch::cat({Reference_State, Current_State}, 0);
    InvNet.zero_grad();
    return (InvNet.forward(Network_Input_Inv)+1)/2;
}

void Update_Weights_InvModel(const torch::Tensor& Current_State,
                             const torch::Tensor& Motor_Input)
{
/////////////////////////////////////////////////////////////////
////////////// Update the weight of the inverse /////////////////
/////////////////////////////////////////////////////////////////
    auto C_a = Current_State.accessor<double,1>();
    auto R_a = Reference_state_Prev.accessor<double,1>();
    auto MI_a =Motor_Input.accessor<double,1>();
    torch::nn::MSELoss lossInv;
    torch::Tensor Inv_loss = lossInv(Current_State, Reference_state_Prev.detach());
    Inv_loss.backward();
    Inv_Optim.step();

    std::ofstream foutInv;  // Create Object of ofstream
    foutInv.open (NetworkInv , std::ios::app);
    foutInv<<R_a[1]<<"\t"<<R_a[3]<<"\t"<<C_a[1] <<"\t"<<C_a[3]<<"\t"<<Inv_loss.template item<float>()<<"\t"<<MI_a[1]*2-1<<"\n";
    foutInv.close(); // Closing the file
}

void FeedForModel(
        const torch::Tensor& Current_State,
        const torch::Tensor& Motor_Input
//        ,const std::vector<std::shared_ptr<Actuator>> &_actuators
)
{
    torch::Tensor Network_Input_FeedFor = torch::cat({Motor_Input, Current_State},0);

    FeedForNet.zero_grad();
    Predicted_state_Prev = (FeedForNet.forward(Network_Input_FeedFor.detach())+1)/2;
}

void Update_Weights_FeedForModel(const torch::Tensor& Current_State,
                                 const torch::Tensor& Motor_Input)
{

    torch::nn::MSELoss lossFor;
    torch::Tensor FeedFor_loss = lossFor(Predicted_state_Prev, Current_State.clone().detach());
    FeedFor_loss.backward();
    FeedFor_Optim.step();

    auto P_a = Predicted_state_Prev.accessor<double,1>();
    auto C_a = Current_State.accessor<double,1>();

    std::ofstream fout;  // Create Object of ofstream
    fout.open (NetworkFor , std::ios::app);
    fout<<P_a[1]<<"\t"<<P_a[3]<<"\t"<<C_a[1] <<"\t"<<C_a[3]<<"\t"<<FeedFor_loss.template item<float>()<<"\n";
    fout.close(); // Closing the file


}



int main(){
    std::ofstream ofs;
    ofs.open(NetworkFor, std::ofstream::out | std::ofstream::trunc);
    ofs.close();
    ofs.open(NetworkInv, std::ofstream::out | std::ofstream::trunc);
    ofs.close();


    torch::Tensor current_state = Predicted_state_Prev+0.0;
    auto options = torch::TensorOptions().dtype(torch::kFloat64);

    std::time_t result = std::time(nullptr);
    std::cout << current_state << "\n" << Predicted_state_Prev << "\n" << std::asctime(std::localtime(&result));

    FeedForNet.to(torch::kDouble);
    InvNet.to(torch::kDouble);


    for(double t=0; t < 5000;) {
        double data_input[]={ (cos(t*freq+phase)+sin(t*freq*2.5-phase)+2)/4, (-cos(t*freq+phase)-sin(t*freq*2.5-phase)+2)/4, -
                                                                                                                                     ((sin(t*freq+phase)*freq+cos(t*freq*2.5-phase)*freq*2.5)/4+.2)*2.5, ((sin(t*freq+phase)*freq-cos(t*freq*2.5-phase)*freq*2.5)/4+.2)*2.5};


        torch::Tensor reference_state = torch::from_blob(data_input,{2*actuatorsize}, options);
//        std::cout<< current_state-(Predicted_state_Prev-Reference_state_Prev);
        torch::Tensor fb = (Predicted_state_Prev-current_state).detach();


        torch::Tensor motor_input = InvModel(current_state, reference_state+fb, fb);


        FeedForModel( current_state, motor_input);

        torch::Tensor fb2 = (reference_state-Predicted_state_Prev).detach();
        motor_input = motor_input+fb.reshape({2,actuatorsize}).sum(0)
                      + fb2.reshape({2,actuatorsize}).sum(0);
//
        torch::Tensor statedot = (torch::cat({torch::clamp(
                current_state.narrow(0,actuatorsize,actuatorsize)*2-1, -1, 1),
                                              (torch::clamp(motor_input,0,1)*2-1)},
                                             0))*0.2;
//        torch::Tensor statedot({(-sin(t*freq+phase)*freq+1)/2, (-sin(t*freq+phase)*freq+1)/2});
//        torch::Tensor statedot = (current_state-reference_state);
//        std::cout << current_state;
        current_state = clamp(current_state+statedot, 0 , 1);

        Update_Weights_FeedForModel(current_state,motor_input);
        Update_Weights_InvModel(current_state,motor_input);

        Reference_state_Prev = reference_state;
        current_state = current_state.detach();
//        current_state.to(options);
//        std::cout << "\n\nData_out: \n" << data_output[0] << " " << data_output[1] << "\ncurrent_state: \n"<< current_state;
//        std::cout << current_state;
        t = t+1;

    }

    result = std::time(nullptr);
    std::cout << std::asctime(std::localtime(&result));
};