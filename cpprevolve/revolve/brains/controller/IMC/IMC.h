//
//
//


#include "../sensors/Sensor.h"
#include "../actuators/Actuator.h"
#include "../Controller.h"
#include "FeedForwardNetwork.h"
#include "InverseNetwork.h"
#include "../DifferentialCPG.h"

// libtorch has some nasty defines that break libcmaes, remove them after each inclusion
#include "torch/torch.h"
#undef LOG_IF
#undef LOG

namespace revolve {

class IMC : public Controller
{
public:
    struct IMCParams {
        double learning_rate = 5e-2;
        double beta1 = 0.9;
        double beta2 = 0.99;
        double weight_decay = 0.001;
        int window_length = 60;
        bool restore_checkpoint = false;
        bool save_checkpoint = true;
        std::string model_name;
        };
    /// \brief Constructor
    /// \param[in] _controller Reference
    /// \param[in] _actuators Reference to a actuator list
    /// \param[in] params Parameters for the IMC learning rate/beta_factor/restore_checkpoint
    IMC(
            std::unique_ptr<::revolve::Controller> wrapped_controller,
            const std::vector<std::shared_ptr<Actuator>> &_actuators,
            const IMC::IMCParams &params);

    /// \brief Inverse Model function
    torch::Tensor InverseModel(
            const torch::Tensor& Current_State,
            const torch::Tensor& Reference_State);

    /// \brief FeedForward Model function
    torch::Tensor FeedForModel(
            const torch::Tensor& Current_State,
            const torch::Tensor& Motor_Input);

    /// \brief Generic functions
    void Update_Weights(
            const torch::Tensor& Current_State,
            const torch::Tensor& Motor_Input);

    void Step(
            const torch::Tensor& current_state,
            const torch::Tensor& reference_state,
            const std::vector<std::shared_ptr<Actuator>> &_actuators,
            double dt);

    void update(
            const std::vector<std::shared_ptr<Actuator>> &actuators,
            const std::vector<std::shared_ptr<Sensor>> &sensors,
            double time,
            double step
            ) override;

    void Save_Progress(std::string model_name);
    void Load_Progress(std::string model_name);

    DifferentialCPG* into_DifferentialCPG() override { return this->_wrapped_controller->into_DifferentialCPG(); }

private:
    class FakeActuator: public Actuator {
        double *const buffer;

    public:
        explicit FakeActuator(double *const buffer, const std::shared_ptr<Actuator> &wrapped)
            : Actuator(wrapped->n_outputs(), wrapped->coordinate_x(), wrapped->coordinate_y(), wrapped->coordinate_z())
            , buffer(buffer)
        {};

        double Current_State( StateType /*type*/ ) override { return 0.0; }

        void write(const double *output, double /*step*/) override
        {
            for (unsigned int i=0; i<n_outputs(); i++) {
                this->buffer[i] = output[i];
            }
        }
    };


protected:
    std::unique_ptr<::revolve::Controller> _wrapped_controller;

    /// \brief Inverse Network
    InverseNetwork InverseNet;

    /// \brief Loaded Inverse weights
    std::unique_ptr<torch::optim::Adam> Inverse_Optim;

    /// \brief Feed Forward Network
    FeedForwardNetwork FeedForNet;

    /// \brief Loaded Feed Forward weights
    std::unique_ptr<torch::optim::Adam> FeedFor_Optim;

    /// \brief Previous reference state
    torch::Tensor Reference_state_Prev;

    /// \brief Previous reference state
    torch::Tensor Predicted_state_Prev;

    torch::Tensor Motor_Input_Prev;
    torch::Tensor Motor_Input_Prev_fb;
    torch::Tensor Current_State_Prev;

    torch::Tensor State_Memory;
    torch::Tensor Reference_Memory;
    bool Save_Check;
    std::string model_name;

};

}


