//
// Created by fuda on 16-03-20.
//

//
// Created by fuda on 25-02-20.
//
//#pragma once
#include <memory>
#include <stdexcept>

#include <gazebo/sensors/sensors.hh>
#include <gazebo/gazebo.hh>
#include <gazebo/physics/physics.hh>
#include <gazebo/common/common.hh>
#include <gazebo/msgs/msgs.hh>

#include <torch/torch.h>

//#include "../plugin/RobotController.h"

#include "IMC.h"
#include "torch/torch.h"

#include "revolve/brains/learner/EvaluationReporter.h"
#include "revolve/brains/controller/sensors/Sensor.h"
#include "revolve/brains/controller/actuators/Actuator.h"
#include "revolve/brains/learner/Learner.h"
#include "revolve/brains/learner/Evaluator.h"
#include "revolve/brains/learner/NoLearner.h"
#include "revolve/brains/learner/BayesianOptimizer.h"
#include "revolve/brains/learner/HyperNEAT.h"
#include "revolve/brains/controller/Controller.h"



#include <iostream>
#include <memory>
#include <stdexcept>
#include <multineat/Genome.h>
#include <multineat/Population.h>

#include <vector>
#include <cpprevolve/revolve/gazebo/brains/RLPower.h>
#include <cpprevolve/revolve/gazebo/brains/DifferentialCPPNCPG.h>
#include "revolve/gazebo/brains/GazeboReporter.h"
#include "revolve/gazebo/brains/Brains.h"
//#include <revolve/gazebo/brains/Evaluator.h>
#include "revolve/gazebo/Types.h"
#include <cpprevolve/revolve/gazebo/brains/Evaluator.h>


const std::string sdfPath("/home/fuda/Projects/revolve/experiments/examples/yaml/Single_link.yaml.sdf");

// load and check sdf file
sdf::SDFPtr sdfElement(new sdf::SDF());



std::unique_ptr<::revolve::gazebo::Evaluator> evaluator;
std::unique_ptr<::revolve::EvaluationReporter> reporter;
std::shared_ptr<::revolve::gazebo::GazeboReporter> gazebo_reporter;
/// \brief Networking node
::gazebo::transport::NodePtr node_;


/// \brief Motors in this model
//std::vector< std::shared_ptr< revolve::Actuator > > motors_;
std::vector<revolve::gazebo::MotorPtr> motors_;

/// \brief Sensors in this model
//std::vector< std::shared_ptr< revolve::Sensor > > sensors_;
std::vector<revolve::gazebo::SensorPtr> sensors_;

/// \brief Pointer to the model
::gazebo::physics::ModelPtr model_;

/// \brief Learner for the brain controlling this model
std::unique_ptr<::revolve::Learner> learner;


//namespace  revolve

int main ()
{
    sdf::init(sdfElement);
    if (!sdf::readFile(sdfPath, sdfElement))
    {
        std::cerr << sdfPath << " is not a valid SDF file!" << std::endl;
    }
    // start parsing model
    const sdf::ElementPtr _sdf = sdfElement->Root();

    if (not _sdf->HasElement("rv:brain")) {
    std::cerr << "No robot brain detected, this is probably an error."
    << std::endl;

    }

    auto brain_sdf = _sdf->GetElement("rv:brain");
    auto controller_type = brain_sdf->GetElement("rv:controller")->GetAttribute("type")->GetAsString();
    //    auto IMC_params = brain_sdf->GetElement("rv:IMC")->GetElement("rv:params");
    auto learner_type = brain_sdf->GetElement("rv:learner")->GetAttribute("type")->GetAsString();
    std::cout << "Loading controller " << controller_type << " and learner " << learner_type << std::endl;


    //TODO parameters from SDF
    const double evaluation_rate = 15.0;
    const unsigned int n_learning_evaluations = 50;

    evaluator = std::make_unique< revolve::gazebo::Evaluator >(evaluation_rate, true, model_);

    // aggregated reporter
    std::unique_ptr<revolve::AggregatedReporter> aggregated_reporter(new revolve::AggregatedReporter(model_->GetName()));
    // std::cout reporter
    aggregated_reporter->create<::revolve::PrintReporter>();
    // gazebo network publisher reporter
    gazebo_reporter.reset(new ::revolve::gazebo::GazeboReporter(aggregated_reporter->robot_id, node_));
    aggregated_reporter->append(gazebo_reporter);

    reporter = std::move(aggregated_reporter);

    // SELECT CONTROLLER ------------------------------------------------------
    std::unique_ptr<::revolve::Controller> controller;

    if ("ann" == controller_type) {
        controller = std::make_unique<revolve::gazebo::NeuralNetwork>(model_, brain_sdf, motors_, sensors_);
    } else if ("spline" == controller_type) {
        if (not motors_.empty()) {
            controller = std::make_unique<revolve::gazebo::RLPower>(model_, brain_sdf, motors_, sensors_);
        }
    } else if ("cpg" == controller_type) {
        controller = std::make_unique<revolve::gazebo::DifferentialCPG>(brain_sdf, motors_);
    } else if ("cppn-cpg") {
        controller = std::make_unique<revolve::gazebo::DifferentialCPPNCPG>(brain_sdf, motors_);
    } else {
        throw std::runtime_error("Robot brain: Controller \"" + controller_type + "\" is not supported.");
    }
    std::cout << "initialized the controller" << std::endl;
    // ================= INITIALIZE IMC ====================
    revolve::IMC::IMCParams imc_params = revolve::IMC::IMCParams();
    std::unique_ptr<::revolve::Controller> controller2;
    std::unique_ptr<::revolve::Controller> imc;
    imc = std::make_unique<revolve::IMC>(std::move(controller), motors_, imc_params);

    controller2 = std::move(imc);


    // SELECT LEARNER ---------------------------------------------------------
    if ("offline" == learner_type) {
    learner = std::make_unique<revolve::NoLearner<revolve::Controller>>(std::move(controller));
    } else if ("rlpower" == learner_type) {
    //TODO make RLPower generic
    if ("spline" != controller_type) {
    throw std::runtime_error("Robot brain: Learner RLPower not supported for \"" + controller_type + "\" controller.");
    }
    learner = std::make_unique<revolve::NoLearner<revolve::Controller>>(std::move(controller));
    } else if ("bo" == learner_type) {
    learner = std::make_unique<revolve::BayesianOptimizer>(
            std::move(controller),
            evaluator.get(),
            reporter.get(),
            evaluation_rate,
            n_learning_evaluations);
    } else if ("hyperneat" == learner_type) {
    NEAT::Parameters neat_params = NEAT::Parameters();

    const sdf::ElementPtr learner_sdf = brain_sdf->GetElement("rv:learner")->GetElement("rv:params");


    #define WRITE_DOUBLE_PARAM(x)   std::cout << #x << " is set to: " << learner_sdf->GetAttribute(#x)->GetAsString() << std::endl; neat_params.x = stod(learner_sdf->GetAttribute(#x)->GetAsString());
    #define CHECK_PARAM(x)   {stod(std::to_string(neat_params.x))==stod(learner_sdf->GetAttribute(#x)->GetAsString()) ? std::cout << std::left <<#x << " is set to: Default" << std::endl : WRITE_DOUBLE_PARAM(x)}
    CHECK_PARAM(PopulationSize)
    CHECK_PARAM(WeightDiffCoeff)
    CHECK_PARAM(CompatTreshold)
    CHECK_PARAM(YoungAgeTreshold)
    CHECK_PARAM(OldAgeTreshold)
    CHECK_PARAM(MinSpecies)
    CHECK_PARAM(MaxSpecies)
    CHECK_PARAM(RouletteWheelSelection)
    CHECK_PARAM(RecurrentProb)
    CHECK_PARAM(OverallMutationRate)
    CHECK_PARAM(ArchiveEnforcement)
    CHECK_PARAM(MutateWeightsProb)
    CHECK_PARAM(WeightMutationMaxPower)
    CHECK_PARAM(WeightReplacementMaxPower)
    CHECK_PARAM(MutateWeightsSevereProb)
    CHECK_PARAM(WeightMutationRate)
    CHECK_PARAM(WeightReplacementRate)
    CHECK_PARAM(MaxWeight)
    CHECK_PARAM(MutateAddNeuronProb)
    CHECK_PARAM(MutateAddLinkProb)
    CHECK_PARAM(MutateRemLinkProb)
    CHECK_PARAM(MinActivationA)
    CHECK_PARAM(MaxActivationA)
    CHECK_PARAM(ActivationFunction_SignedSigmoid_Prob)
    CHECK_PARAM(ActivationFunction_UnsignedSigmoid_Prob)
    CHECK_PARAM(ActivationFunction_Tanh_Prob)
    CHECK_PARAM(ActivationFunction_SignedStep_Prob)
    CHECK_PARAM(CrossoverRate)
    CHECK_PARAM(MultipointCrossoverRate)
    CHECK_PARAM(SurvivalRate)
    CHECK_PARAM(MutateNeuronTraitsProb)
    CHECK_PARAM(MutateLinkTraitsProb)
    #undef CHECK_PARAM
    #undef WRITE_DOUBLE_PARAM

    neat_params.DynamicCompatibility = (learner_sdf->GetAttribute("DynamicCompatibility")->GetAsString() == "true");
    neat_params.NormalizeGenomeSize = (learner_sdf->GetAttribute("NormalizeGenomeSize")->GetAsString() == "true");
    neat_params.AllowLoops = (learner_sdf->GetAttribute("AllowLoops")->GetAsString() == "true");
    neat_params.AllowClones = (learner_sdf->GetAttribute("AllowClones")->GetAsString() == "true");

    int seed = 0;

    learner = std::make_unique<revolve::HyperNEAT>(
            std::move(controller),
            evaluator.get(),
            reporter.get(),
            neat_params,
            seed,
            evaluation_rate,
            n_learning_evaluations);
    } else {
    throw std::runtime_error("Robot brain: Learner \"" + learner_type + "\" is not supported.");
    }
}
