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
 * Date: 10-09-18
 *
 */

#include <cmath>
#include <gazebo/physics/Model.hh>
#include <revolve/gazebo/motors/JointMotor.h>
#include <revolve/brains/learner/Evaluator.h>


#include "Evaluator.h"

using namespace revolve::gazebo;

/////////////////////////////////////////////////
double Evaluator::measure_distance(
    const ignition::math::Pose3d &_pose1,
    const ignition::math::Pose3d &_pose2)
{
  return std::sqrt(std::pow(_pose1.Pos().X() - _pose2.Pos().X(), 2) +
                   std::pow(_pose1.Pos().Y() - _pose2.Pos().Y(), 2));
}

/////////////////////////////////////////////////
Evaluator::Evaluator(const double evaluation_rate,
                     const bool reset_robot_position,
                     const ::gazebo::physics::ModelPtr &robot,
                     const double step_saving_rate)
        : ::revolve::Evaluator()
        , evaluation_rate_(evaluation_rate)
        , last_step_time(-1)
        , step_saving_rate(step_saving_rate)
        , step_poses(0)
        , reset_robot_position(reset_robot_position)
        , robot(robot)
{
  this->current_position_.Reset();
  this->previous_position_.Reset();
  this->start_position_.Reset();
  this->locomotion_type = "gait"; // {turing_left,directed, gait}
  this->path_length = 0.0;

  std::string model_name = robot->GetName();
  this->output_dir = "./experiments/IMC/output"+model_name;

//  std::ofstream decom_file;
//  decom_file.open(this->output_dir+"/fitness_decom.txt", std::ofstream::out | std::ofstream::trunc);
//  decom_file.close();
  std::cout<<"Loading evaluator with task: "+this->locomotion_type<<std::endl;
}

/////////////////////////////////////////////////
Evaluator::~Evaluator() = default;

/////////////////////////////////////////////////
void Evaluator::reset()
{
    // Reset robot if opted to do
    if (this->reset_robot_position) {
        //this->robot->Reset();
        ::gazebo::physics::ModelPtr _robot = robot.lock();
        _robot->ResetPhysicsStates();
        auto start_pose = ::ignition::math::Pose3d();
        start_pose.Set(0.0, 0.0, 0.1, 0.0, 0.0, -.1);
        for (const auto &joint_ : _robot->GetJoints()) {
            std::string joint_name = joint_->GetScopedName();
            _robot->SetJointPosition(joint_name, 0.0);
            joint_->SetPosition(0, 0.0);
        }
        _robot->SetWorldPose(start_pose);
        for (const auto& joint_ : _robot->GetJoints()) {
            std::string joint_name = joint_->GetScopedName();
            _robot->SetJointPosition(joint_name, 0.0);
            joint_->SetPosition(0, 0.0);

        }
        _robot->Update();
        this->current_position_ = start_pose;
    }

    this->step_poses.clear(); //cleared to null
    this->path_length = 0.0;
    this->last_step_time = 0.0;
    this->start_position_ = this->current_position_;
}

/////////////////////////////////////////////////
double Evaluator::fitness()
{
  double fitness_value = 0.0;
  if(this->locomotion_type == "gait")
  {
    double dS;
    dS = std::sqrt(std::pow(this->start_position_.Pos().X() -
                            this->current_position_.Pos().X(), 2) +
                   std::pow(this->start_position_.Pos().Y() -
                            this->current_position_.Pos().Y(), 2));
    fitness_value = dS / this->evaluation_rate_;
    if(fitness_value > 5e-11){
        std::ofstream fitness_file;
        fitness_file.open(this->output_dir + "/fitness_decom.txt", std::ios::app);
        fitness_file << std::fixed
                     <<fitness_value
                     <<","<<std::sqrt(std::pow(this->start_position_.Pos().X() - this->current_position_.Pos().X(), 2))
                     <<","<<std::sqrt(std::pow(this->start_position_.Pos().Y() - this->current_position_.Pos().Y(), 2))
                     <<std::endl;
        fitness_file.close();
      }
  }
  else if (this->locomotion_type == "directed")
  {

    this->step_poses.push_back(this->current_position_);
    //step_poses: x y z roll pitch yaw
    for (size_t i=1; i < this->step_poses.size(); i++)
    {
      const auto &pose_i_1 = this->step_poses[i-1];
      const auto &pose_i = this->step_poses[i];
      this->path_length += Evaluator::measure_distance(pose_i_1, pose_i);
    }

    ////********** directed locomotion fitness function **********////
    //directions(forward) of heads are the orientation(+x axis) - 1.570796
    double beta0 = this->start_position_.Rot().Yaw()- M_PI/2.0;
    if (beta0 < - M_PI) //always less than pi (beta0 + max(40degree) < pi)
    {
      beta0 = 2 * M_PI - std::abs(beta0);
    }

    double beta1 = std::atan2(
        this->current_position_.Pos().Y() - this->start_position_.Pos().Y(),
        this->current_position_.Pos().X() - this->start_position_.Pos().X());

    double alpha;
    if (std::abs(beta1 - beta0) > M_PI)
    {
      alpha = 2 * M_PI - std::abs(beta1) - std::abs(beta0);
    } else
    {
      alpha = std::abs(beta1 - beta0);
    }

    double A = std::tan(beta0);
    double B = this->start_position_.Pos().Y()
               - A * this->start_position_.Pos().X();

    double X_p = (A * (this->current_position_.Pos().Y() - B)
                  + this->current_position_.Pos().X()) / (A * A + 1);
    double Y_p = A * X_p + B;

    //calculate the fitness_direction based on dist_projection, alpha, penalty
    double dist_projection;
    double dist_penalty;
    double penalty;
    double fitness_direction;
    double ksi = 1.0;
    if (alpha > 0.5 * M_PI)
    {
      dist_projection = -std::sqrt(
          std::pow((this->start_position_.Pos().X() - X_p), 2.0) +
          std::pow((this->start_position_.Pos().Y() - Y_p), 2.0));
      dist_penalty = std::sqrt(
          std::pow((this->current_position_.Pos().X() - X_p), 2.0) +
          std::pow((this->current_position_.Pos().Y() - Y_p), 2.0));
      penalty = 0.01 * dist_penalty;
    }
    else
    {
      dist_projection = std::sqrt(
          std::pow((this->start_position_.Pos().X() - X_p), 2.0) +
          std::pow((this->start_position_.Pos().Y() - Y_p), 2.0));
      dist_penalty = std::sqrt(
          std::pow((this->current_position_.Pos().X() - X_p), 2.0) +
          std::pow((this->current_position_.Pos().Y() - Y_p), 2.0));
      penalty = 0.01 * dist_penalty;
    }

    //fitness_direction = dist_projection / (alpha + ksi) - penalty;
//    fitness_direction = (dist_projection / (alpha + ksi) - penalty);
    fitness_direction = dist_projection*std::abs(dist_projection) - dist_penalty*dist_penalty;
    fitness_value = fitness_direction;


    double tot_dist = std::sqrt(
              std::pow(dist_projection, 2.0) + std::pow(dist_penalty, 2.0));

    // Write fitness to file
    std::ofstream fitness_file;
    fitness_file.open(this->output_dir + "/fitness_decom.txt", std::ios::app);
    fitness_file << std::fixed
                 << fitness_value
                 <<","<<dist_penalty
                 <<","<<dist_projection
                 <<","<<tot_dist
                 <<","<<path_length
                 <<std::endl;

    fitness_file.close();
  }
  else if(this->locomotion_type == "turing_left") //anticlockwise
  {
      double orientations = 0.0;
      double delta_orientations = 0.0;
      double dS = 0.0;
      for(int i = 1; i < this->step_poses.size(); i++)
      {
          const auto &pose_i_1 = this->step_poses[i-1];
          const auto &pose_i = this->step_poses[i];

          dS = dS + Evaluator::measure_distance(pose_i_1, pose_i);

          double angle_i = pose_i.Rot().Yaw();
          double angle_i_1 = pose_i_1.Rot().Yaw();
          if(angle_i_1 > M_PI_2 and angle_i < - M_PI_2 ) // rotating left
          {
              delta_orientations = 2.0 * M_PI + angle_i - angle_i_1;
          }
          else if((angle_i_1 < - M_PI_2) and (angle_i > M_PI_2))
          {
              delta_orientations = - (2.0 * M_PI - angle_i + angle_i_1);
          }
          else
          {
              delta_orientations = angle_i - angle_i_1;
          }
          orientations += delta_orientations;

      }
      std::cout << "orientations: " << orientations << " dS: " << dS << std::endl;
      double factor_orien_ds = 3.0; //TODO param
      fitness_value = orientations - factor_orien_ds * dS; //dS in (0, 1.5) in 30s
    }

    return fitness_value;
}

// update is always running in the loop
void Evaluator::simulation_update(const ignition::math::Pose3d &pose,
                                  const double time,
                                  const double step)
{
  //  this->path_length += measure_distance(current_position_, pose);
  this->previous_position_ = current_position_;
  this->current_position_ = pose;

  //If `last_step_time` is not initialized, do the initialization now
  if (this->last_step_time < 0)
  {
    this->last_step_time = time; // 0.005
    this->step_poses.push_back(pose);
  }

  //save the startPosition in the beginning of each iteration
  if (this->last_step_time < 0.001) // 0.001 < 0.005
  {
    this->step_poses.push_back(pose);
    this->last_step_time = time;
  }
  //update information each step
  if ((time - this->last_step_time) > this->evaluation_rate_ * this->step_saving_rate)
  {
    this->step_poses.push_back(pose);
    this->last_step_time = time;
  };
}
