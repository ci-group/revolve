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

#include "Evaluator.h"

#include <revolve/gazebo/battery/Battery.h>

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
Evaluator::Evaluator(std::shared_ptr<::revolve::gazebo::Battery> battery,
                     const double _evaluationRate,
                     const double step_saving_rate
                     )
    : last_step_time(-1)
    , step_saving_rate(step_saving_rate)
    , step_poses(0)
    , battery_(battery)
{
  assert(_evaluationRate > 0 and "`_evaluationRate` should be greater than 0");
  this->evaluation_rate_ = _evaluationRate;

  this->current_position_.Reset();
  this->previous_position_.Reset();
  this->start_position_.Reset();
  this->locomotion_type = "directed"; // {directed, gait, battery} // STEP 3
  this->path_length = 0.0;
}

/////////////////////////////////////////////////
Evaluator::~Evaluator() = default;

/////////////////////////////////////////////////
void Evaluator::Reset()
{
  this->step_poses.clear(); //cleared to null
  this->path_length = 0.0;
  this->last_step_time = 0.0;
  this->start_position_ = this->current_position_;
}

/////////////////////////////////////////////////
double Evaluator::Fitness()
{
  double fitness_value = 0.0;
  double speed;
  if(this->locomotion_type == "gait")
  {
    double dS;
    dS = std::sqrt(std::pow(this->previous_position_.Pos().X() -
                            this->current_position_.Pos().X(), 2) +
                   std::pow(this->previous_position_.Pos().Y() -
                            this->current_position_.Pos().Y(), 2));
    fitness_value = dS / this->evaluation_rate_;
  }
  else if (this->locomotion_type == "directed")
  {
    this->step_poses.push_back(this->current_position_);
    //step_poses: x y z roll pitch yaw
    for (int i=1; i < this->step_poses.size(); i++)
    {
      const auto &pose_i_1 = this->step_poses[i-1];
      const auto &pose_i = this->step_poses[i];
      this->path_length += Evaluator::measure_distance(pose_i_1, pose_i);
      //save coordinations to coordinates.txt
      std::ofstream coordinates;
      coordinates.open(this->directory_name + "/coordinates.txt",std::ios::app);

      if(i == 1)
      {
          coordinates << std::fixed << start_position_.Pos().X() << " " << start_position_.Pos().Y() << std::endl;
      }
      coordinates << std::fixed << pose_i.Pos().X() << " " << pose_i.Pos().Y() << std::endl;
    }
    // save the speed to speed.txt
    std::ofstream speeds;
    speeds.open(this->directory_name + "/speed.txt",std::ios::app);
    speed = this->path_length / evaluation_rate_;
    speeds << speed << std::endl;

      ////********** directed locomotion fitness function **********////
    //directions(forward) of heads are the orientation(+x axis) - 1.570796
    double beta0 = this->start_position_.Rot().Yaw()- M_PI/2.0;
    if (beta0 < - M_PI) //always less than pi (beta0 + max(40degree) < pi)
    {
      beta0 = 2 * M_PI - std::abs(beta0);
    }

    //save direction to coordinates.txt: This is used to make Figure 8
    std::ofstream coordinates;
    coordinates.open(this->directory_name + "/coordinates.txt",std::ios::app);
    coordinates << std::fixed << beta0 << std::endl;

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
    fitness_direction = std::abs(dist_projection) / path_length *
                        (dist_projection / (alpha + ksi) - penalty);
    fitness_value = fitness_direction;
  }
  else if (this->locomotion_type == "battery")
  {
      this->step_poses.push_back(this->current_position_);
      //step_poses: x y z roll pitch yaw
      for (int i=1; i < this->step_poses.size(); i++)
      {
          const auto &pose_i_1 = this->step_poses[i-1];
          const auto &pose_i = this->step_poses[i];
          this->path_length += Evaluator::measure_distance(pose_i_1, pose_i);
          //save coordinations to coordinates.txt
          std::ofstream coordinates;
          coordinates.open(this->directory_name + "/coordinates.txt",std::ios::app);

          if(i == 1)
          {
              coordinates << std::fixed << start_position_.Pos().X() << " " << start_position_.Pos().Y() << std::endl;
          }
          coordinates << std::fixed << pose_i.Pos().X() << " " << pose_i.Pos().Y() << std::endl;
      }
      // save the speed to speed.txt
      std::ofstream speeds;
      speeds.open(this->directory_name + "/speed.txt",std::ios::app);
      speed = this->path_length / evaluation_rate_;
      speeds << speed << std::endl;

      ////********** directed locomotion fitness function **********////
      //directions(forward) of heads are the orientation(+x axis) - 1.570796
      double beta0 = this->start_position_.Rot().Yaw()- M_PI/2.0;
      if (beta0 < - M_PI) //always less than pi (beta0 + max(40degree) < pi)
      {
          beta0 = 2 * M_PI - std::abs(beta0);
      }

      //save direction to coordinates.txt: This is used to make Figure 8
      std::ofstream coordinates;
      coordinates.open(this->directory_name + "/coordinates.txt",std::ios::app);
      coordinates << std::fixed << beta0 << std::endl;

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
      fitness_direction = std::abs(dist_projection) / path_length *
                          (dist_projection / (alpha + ksi) - penalty);

      double w = 0.03;
      std::cout << "f:\t" << fitness_direction << "\tP:\t" << (this->battery_->current_charge * w) << std::endl;
      fitness_value = fitness_direction + (this->battery_->current_charge * w);
      this->battery_->current_charge = 0; /// reseting the charge of the robot
  }
  else if (this->locomotion_type == "battery_targeted")
  {
      // old_f = (D_p/D) * b -[ (1 - (D_p/D) ) * (b_t - (len * size(13-34) * P) ) ]

      // new_f = (D_p/D) * b -[ (1 - (D_p/D) ) * (b_t + P) ) ]
      double initial_battery = 1; // b      -> initial battery level. 1 (100%)
      double battery_time = 0.15;   // b_t    -> battery drainage, how much battery robot loses when idle (over time)
      double distance_projection;   // D_p    -> distance projection, the path the robot takes
      double shortest_distance;     // D      -> the shortest path to target
                                    // len    -> this->path_length
      double robot_size = 17;       // size   -> the size of the robot TODO get the size from the robot manager
      double power_used = this->battery_->current_charge;     // P      -> the amount of power used by each servo motor

      // initializing the coordinates of the charging station (±1.6, ±1.6, 0.12) (x,y,z)
      ignition::math::Pose3d target_coord;
      target_coord.Pos().X() = 1.6;
      target_coord.Pos().Y() = 1.6;
      target_coord.Pos().Z() = 0.12;

      // calculating the shortest/initial distance
      shortest_distance = measure_distance(this->start_position_, target_coord);




      // calculating the path length
      this->step_poses.push_back(this->current_position_);
      //step_poses: x y z roll pitch yaw

//    std::cout << "step_poses.size(): " << step_poses.size() << " ";

      for (int i=1; i < this->step_poses.size(); i++)
      {
          const auto &pose_i_1 = this->step_poses[i-1];
          const auto &pose_i = this->step_poses[i];
          this->path_length += Evaluator::measure_distance(pose_i_1, pose_i);
          //save coordinations to coordinates.txt
          std::ofstream coordinates;
          coordinates.open(this->directory_name + "/coordinates.txt",std::ios::app);

          if(i == 1)
          {
              start_position_ = pose_i_1;
              coordinates << std::fixed << start_position_.Pos().X() << " " << start_position_.Pos().Y() << std::endl;
          }
          coordinates << std::fixed << pose_i.Pos().X() << " " << pose_i.Pos().Y() << std::endl;
      }


      // calculating the distance projection

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

      //calculate the dist_projection
      if (alpha > 0.5 * M_PI)
      {
          distance_projection = -std::sqrt(
                  std::pow((this->start_position_.Pos().X() - X_p), 2.0) +
                  std::pow((this->start_position_.Pos().Y() - Y_p), 2.0));
      }
      else
      {
          distance_projection = std::sqrt(
                  std::pow((this->start_position_.Pos().X() - X_p), 2.0) +
                  std::pow((this->start_position_.Pos().Y() - Y_p), 2.0));
      }
      // ************************


      //
      //
      // f = P_initial


//      std::cout << "b: " << initial_battery <<  "\n";
//      std::cout << "size: " << robot_size <<  "\n";
//      std::cout << "b_t: " << battery_time <<  "\n";

      std::cout << "D_p: " << distance_projection << "\t";
//      std::cout << "len: " << this->path_length <<  "\n";
//      std::cout << "D: " << shortest_distance <<  "\n";
//      std::cout << "start pos: " << this->start_position_ << std::endl;

      std::cout << "P: " << power_used <<  "\n";

      std::cout << "distance_projection/shortest_distance = " << distance_projection/shortest_distance << std::endl;
      std::cout << "fitness: " << fitness_value <<  "\n";
      this->battery_->current_charge = 0; /// changing its charge to 0 to simulate the reseting of the robot
  }
    exit(0);
  return fitness_value;
}

// update is always running in the loop
void Evaluator::Update(const ignition::math::Pose3d &_pose,
                       const double time,
                       const double step)
{
  //  this->path_length += measure_distance(current_position_, _pose);
  this->previous_position_ = current_position_;
  this->current_position_ = _pose;

  //If `last_step_time` is not initialized, do the initialization now
  if (this->last_step_time < 0)
  {
    this->last_step_time = time; // 0.005
    this->step_poses.push_back(_pose);
  }

  //save the startPosition in the beginning of each iteration
  if (this->last_step_time < 0.001) // 0.001 < 0.005
  {
    this->step_poses.push_back(_pose);
    this->last_step_time = time;
  }
  //update information each step
  if ((time - this->last_step_time) > this->evaluation_rate_ * this->step_saving_rate)
  {
    this->step_poses.push_back(_pose);
    this->last_step_time = time;
  };
}
