#include <cmath>

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
Evaluator::Evaluator(const double _evaluationRate,
                     const double step_saving_rate)
    : last_step_time(-1)
    , step_saving_rate(step_saving_rate)
    , step_poses(0)
{
  assert(_evaluationRate > 0 and "`_evaluationRate` should be greater than 0");
  this->evaluation_rate_ = _evaluationRate;

  this->current_position_.Reset();
  this->previous_position_.Reset();
  this->start_position_.Reset();
  this->locomotion_type = "directed"; // {directed, gait}
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
  if(this->locomotion_type == "gait")
  {
    double dS;
    dS = std::sqrt(std::pow(this->previous_position_.Pos().X() -
                            this->current_position_.Pos().X(), 2) +
                   std::pow(this->previous_position_.Pos().Y() -
                            this->current_position_.Pos().Y(), 2));
    fitness_value = dS / this->evaluation_rate_;
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
