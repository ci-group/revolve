//
// Created by matteo on 14/06/19.
//
#include "IMC.h"
#include "../sensors/Sensor.h"
#include "../actuators/Actuator.h"
#include "../Controller.h"
#include "torch/torch.h"

#include <map>
#include <memory>
#include <utility>
#include "iostream"

const std::string project_root = ".";


using namespace revolve;

IMC::IMC(std::unique_ptr<::revolve::Controller> wrapped_controller,
        const std::vector<std::shared_ptr<Actuator>> &_actuators,
        const IMC::IMCParams &params)
        : Controller(wrapped_controller->controller_type)
        , _wrapped_controller(std::move(wrapped_controller))
        , InverseNet(int(_actuators.size()))
        , Inverse_Optim(nullptr)
        , FeedForNet(int(_actuators.size()))
        , FeedFor_Optim(nullptr)

{
    this->Inverse_Optim = std::make_unique<torch::optim::Adam>(
            this->InverseNet->parameters(),
            torch::optim::AdamOptions(params.learning_rate*2).betas({params.beta1, params.beta2}).weight_decay(params.weight_decay)
    );
    this->FeedFor_Optim = std::make_unique<torch::optim::Adam>(
            this->FeedForNet->parameters(),
            torch::optim::AdamOptions(params.learning_rate).betas({params.beta1, params.beta2}).weight_decay(params.weight_decay)
    );

    this->Reference_state_Prev = torch::ones(_actuators.size()*2, torch::kFloat)*0.5;
    this->Predicted_state_Prev = this->Reference_state_Prev.requires_grad_(true);
    this->Current_State_Prev   = this->Predicted_state_Prev.requires_grad_(true);
    this->Motor_Input_Prev     = torch::ones(_actuators.size(), torch::kFloat)*0.5;
    this->Motor_Input_Prev_fb = this->Motor_Input_Prev;
    this->FeedForNet->to(torch::kDouble);
    this->InverseNet->to(torch::kDouble);

    this->State_Memory      = torch::ones({long(_actuators.size()*2), params.window_length}, torch::kFloat)* 0.5;
    this->Reference_Memory  = torch::ones({long(_actuators.size()*2), params.window_length}, torch::kFloat)* 0.4999/params.window_length;

    this->Save_Check = params.save_checkpoint;
    this->model_name = params.model_name;

    if (params.restore_checkpoint & false) {

        this->Load_Progress(params.model_name);
        bool test_best = false;
        if(test_best){
            this->Save_Check = false;
            for (const auto& param : this->InverseNet->named_parameters()) {
                param->requires_grad_(false);
            }
            for (const auto& param : this->FeedForNet->named_parameters()) {
                param->requires_grad_(false);
            }
            for (int i = 0; i < int(_actuators.size()); ++i) {
                std::ofstream ofs;
                ofs.open(project_root + "/experiments/IMC/output" + this->model_name + "/act_info/A" +
                         std::to_string(i + 1) + ".log", std::ofstream::out | std::ofstream::trunc);
                ofs.close();
            }
        }
    }
    else {
        for (int i = 0; i < int(_actuators.size()); ++i) {
            std::ofstream ofs;
            ofs.open(project_root + "/experiments/IMC/output" + this->model_name + "/act_info/A" +
                     std::to_string(i + 1) + ".log", std::ofstream::out | std::ofstream::trunc);
            ofs.close();
        }
    }
//    std::ofstream ofs;
//    ofs.open(project_root+"/experiments/IMC/output"+this->model_name+"/IMC_time.txt", std::ofstream::out | std::ofstream::trunc);
//    ofs.close();

}


torch::Tensor IMC::InverseModel(
        const torch::Tensor& Current_State,
        const torch::Tensor& Reference_State)
{
    torch::Tensor Network_Input_Inverse = torch::cat({Reference_State, Current_State}, 0).to(torch::kDouble);
    this->InverseNet->zero_grad();
    return (this->InverseNet->forward(Network_Input_Inverse.detach())+1)/2;
}

torch::Tensor IMC::FeedForModel(
        const torch::Tensor& Current_State,
        const torch::Tensor& Motor_Input)
{
    torch::Tensor Model_Input_FeedFor = torch::cat({Motor_Input, Current_State},0).to(torch::kDouble);
    this->FeedForNet->zero_grad();
    return (this->FeedForNet->forward(Model_Input_FeedFor.detach())+1)/2;
}

void IMC::Update_Weights(
        const torch::Tensor& Current_State,
        const torch::Tensor& Motor_Input)
{
    torch::nn::MSELoss MSE_FeedFor_loss;
    torch::Tensor FeedFor_loss = MSE_FeedFor_loss(Current_State.clone().detach(),this->Predicted_state_Prev);
    FeedFor_loss.backward();
    this->FeedFor_Optim->step();

//    std::cout<<"\n\n#### State Memory ####\n"<<this->State_Memory.narrow(1,1,4)<< "\n #### Current State ####\n"<<Current_State<<std::endl;

    this->State_Memory      = torch::cat({this->State_Memory.narrow(1, 1, this->State_Memory.size(1) - 1).detach(),
                                          Current_State.reshape({Motor_Input.size(0) * 2, 1})},1);
    this->Reference_Memory  = torch::cat({this->Reference_Memory.narrow(1,1,this->State_Memory.size(1)-1),
                                          this->Reference_state_Prev.reshape({Motor_Input.size(0)*2,1})},1);

    torch::nn::MSELoss MSE_Inverse_loss;
    torch::Tensor Inverse_loss = MSE_Inverse_loss(this->State_Memory,this->Reference_Memory.detach());
//    torch::Tensor Inverse_loss = MSE_Inverse_loss(Current_State.narrow(0,0,Motor_Input.size(0)),
//            this->Reference_state_Prev.narrow(0,0,Motor_Input.size(0)));//.narrow(0,0,Motor_Input.size(0)).detach())

    Inverse_loss.backward();
    this->Inverse_Optim->step();

//    /// Logging results
//    auto mi_a = this->Motor_Input_Prev.accessor<float,1>();
//    auto fb_a = this->Motor_Input_Prev_fb.accessor<float,1>();
//    auto ps_a = this->Predicted_state_Prev.accessor<float,1>();
//    auto cs_a = this->Current_State_Prev.accessor<float,1>();
//    auto rs_a = this->Reference_state_Prev.accessor<float,1>();
//
//
//    for(int i=0 ; i<Motor_Input.size(0); ++i){
//        std::ofstream ofs;
//        ofs.open(project_root+"/experiments/IMC/output"+this->model_name+"/act_info/A"+std::to_string(i+1)+".log", std::ios::app);
//        ofs<<cs_a[i] <<","<<cs_a[Motor_Input.size(0)+i]<<","
//           <<rs_a[i]<<","<<rs_a[Motor_Input.size(0)+i]<<","
//           <<ps_a[i]<<","<<ps_a[Motor_Input.size(0)+i]<<","
//           <<FeedFor_loss.template item<float>()<<","<<Inverse_loss.template item<float>()<<","<<mi_a[i]<<","<<fb_a[i]<<std::endl;
//        ofs.close();
//    }
}

void IMC::Step(
        const torch::Tensor& current_state,
        const torch::Tensor& reference_state,
        const std::vector<std::shared_ptr<Actuator>> &_actuators,
        double dt)
{
    if(true){
        this->Current_State_Prev = current_state.requires_grad_(true);
        this->Update_Weights(this->Current_State_Prev, this->Motor_Input_Prev);

        torch::Tensor feedback_error = (this->Predicted_state_Prev-current_state).detach();
        torch::Tensor motor_input = this->InverseModel(current_state, reference_state + feedback_error).to(torch::kFloat);

        torch::Tensor predicted_state = FeedForModel(current_state, motor_input).to(torch::kFloat);
        torch::Tensor FeedFor_error = (reference_state-predicted_state).detach();

        torch::Tensor feedback = feedback_error+FeedFor_error;

        motor_input = (motor_input-0.5)*dt+0.5
                      + (feedback.narrow(0,0,int(_actuators.size()))*5.235988*1.0
                         + feedback.narrow(0,int(_actuators.size()),int(_actuators.size()))*1.0)*dt;

        this->Reference_state_Prev = reference_state;
        this->Predicted_state_Prev = predicted_state;
        this->Current_State_Prev = current_state;
        this->Motor_Input_Prev = motor_input.requires_grad_(true);
        this->Motor_Input_Prev_fb = (feedback.narrow(0,0,int(_actuators.size()))*5.235988*2.0
                                     + feedback.narrow(0,int(_actuators.size()),int(_actuators.size()))*2.0)*dt+0.5;

        motor_input = motor_input.to(torch::kDouble);
        unsigned int p = 0;
        for (const auto &actuator: _actuators)
        {
            double *output = motor_input[p].data_ptr<double>();
            actuator->write(output, dt);
            p += 1;
        }
    }
    else{
        torch::Tensor motor_input = reference_state.narrow(0,0,_actuators.size());

//        /// Logging results
//        auto mi_a = this->Motor_Input_Prev.accessor<float,1>();
//        auto fb_a = this->Motor_Input_Prev_fb.accessor<float,1>();
//        auto ps_a = this->Predicted_state_Prev.accessor<float,1>();
//        auto cs_a = this->Current_State_Prev.accessor<float,1>();
//        auto rs_a = this->Reference_state_Prev.accessor<float,1>();
//
//        for(int i=0 ; i<int(_actuators.size()); ++i){
//            std::ofstream ofs;
//            ofs.open(project_root+"/experiments/IMC/output"+this->model_name+"/act_info/A"+std::to_string(i+1)+".log", std::ios::app);
//            ofs<<cs_a[i] <<","<<cs_a[motor_input.size(0)+i]<<","
//               <<rs_a[i]<<","<<rs_a[motor_input.size(0)+i]<<","
//               <<ps_a[i]<<","<<ps_a[motor_input.size(0)+i]<<","
//               <<abs(cs_a[i] - rs_a[i])+abs(cs_a[motor_input.size(0)+i]-rs_a[motor_input.size(0)+i])<<","<<cs_a[i] *0.0<<","<<mi_a[i]<<","<<fb_a[i]
//               <<"\n";
//            ofs.close();
//        }

        this->Reference_state_Prev = reference_state;
        this->Predicted_state_Prev = motor_input*0.0;
        this->Current_State_Prev = current_state;
        this->Motor_Input_Prev = motor_input;
        this->Motor_Input_Prev_fb = motor_input*0.0;

        motor_input = motor_input.to(torch::kDouble);
        unsigned int p = 0;
        for (const auto &actuator: _actuators)
        {
            double *output = motor_input[p].data_ptr<double>();
            actuator->write(output, dt);
            p += 1;
        }
    }
}

void IMC::Save_Progress(std::string model_name)
{
//    this->InverseNet->eval();
    std::cout<<"SAVE IMC NETWORK PROGRESS"<<std::endl;
    std::ifstream net(project_root+"/experiments/IMC/output"+model_name+"/"+model_name+"_Inverse_network.pt");
    if(net) {
        torch::save(this->InverseNet, project_root+"/experiments/IMC/output"+model_name+"/"+model_name+"_Inverse_network.pt");
        torch::save(*this->Inverse_Optim, project_root+"/experiments/IMC/output"+model_name+"/"+model_name+"_Inverse_optimizer.pt");

        torch::save(this->FeedForNet, project_root+"/experiments/IMC/output"+model_name+"/"+model_name+"_FeedForModel_network.pt");
        torch::save(*this->FeedFor_Optim, project_root+"/experiments/IMC/output"+model_name+"/"+model_name+"_FeedForModel_optimizer.pt");
    }
    else {
        this->Save_Check = false;
    }
}

void IMC::Load_Progress(std::string model_name)
{
    std::ifstream net(project_root+"/experiments/IMC/output"+model_name+"/"+model_name+"_Inverse_network.pt");
    if(net) {
        std::cout<<"load IMC"<<std::endl;
        torch::load(this->InverseNet, project_root+"/experiments/IMC/output"+model_name+"/"+model_name+"_Inverse_network.pt");
        torch::load(*this->Inverse_Optim, project_root+"/experiments/IMC/output"+model_name+"/"+model_name+"_Inverse_optimizer.pt");

        torch::load(this->FeedForNet, project_root+"/experiments/IMC/output"+model_name+"/"+model_name+"_FeedForModel_network.pt");
        torch::load(*this->FeedFor_Optim, project_root+"/experiments/IMC/output"+model_name+"/"+model_name+"_FeedForModel_optimizer.pt");
    }
}

void IMC::update(
        const std::vector<std::shared_ptr<Actuator> > &actuators,
        const std::vector<std::shared_ptr<Sensor> > &sensors,
        double time, double dt)
{
    size_t output_size = 0;
    for (const auto &actuator: actuators) {
        output_size += actuator->n_outputs();
    }

    std::vector<double> actuator_buffer(output_size);
    double *actuator_buffer_data_p = actuator_buffer.data();

    size_t output_cursor = 0;
    std::vector<std::shared_ptr<Actuator> > fake_actuators;
    for (const auto &actuator: actuators) {
        const size_t size = actuator->n_outputs();
        fake_actuators.emplace_back(std::make_shared<FakeActuator>(
                actuator_buffer_data_p+output_cursor,
                actuator));
        output_cursor += size;
    }

    this->_wrapped_controller->update(fake_actuators, sensors, time, dt);

    // ================= READ STATE =======================
    std::vector<double> current_state_v;
    current_state_v.reserve(actuators.size()*2);
    for (const auto &actuator: actuators) {
        current_state_v.emplace_back(actuator->Current_State(Actuator::StateType::POSITION)/2+.5);
    }
    for (const auto &actuator: actuators) {
        current_state_v.emplace_back(actuator->Current_State(Actuator::StateType::VELOCITY)/2/5.235988+.5);
    }

    // Current state of the servo motor
    torch::Tensor current_state = torch::tensor(current_state_v);

    // State you want to go to (controller output)
    torch::Tensor reference_state = torch::tensor(actuator_buffer)/2+.5;
//    if(time<=2*dt){
//        reference_state= (reference_state-.5)*time/(3*dt)+.5;
//    }

    torch::Tensor reference_state_dot = ((reference_state-this->Reference_state_Prev.narrow(0,0,actuators.size()))/dt/5.235988+.5).clamp(0,1);
    reference_state = torch::cat({reference_state,reference_state_dot},0);

    this->Step(current_state, reference_state, actuators, dt);

    if((std::fmod(time,60.0) == 0) & this->Save_Check){
        this->Save_Progress(this->model_name);
        if(time == dt){
            for(const auto& pair : this->InverseNet->named_parameters().pairs()){
                this->InverseNet->named_parameters().find(pair.first)->
                        set_requires_grad(pair.first.find("ut") == std::string::npos);
            }
            for(const auto& pair : this->InverseNet->named_parameters().pairs()){
                this->InverseNet->named_parameters().find(pair.first)->
                        set_requires_grad(pair.first.find("ut") == std::string::npos);
            }
        }
    }
}