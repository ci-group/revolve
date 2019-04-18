//
// Created by Gongjin Lan on 4/17/19.
//

#include "EvaluatorDirectedLocomotion.h"

#include <cmath>

using namespace revolve::gazebo;

EvaluatorDirectedLocomotion::EvaluatorDirectedLocomotion(
    const double _evaluationRate,
    const double step_saving_rate)
  : Evaluator(_evaluationRate)
  , last_step_time(-1)
  , step_saving_rate(step_saving_rate)
  , step_poses(0)
{

}

EvaluatorDirectedLocomotion::~EvaluatorDirectedLocomotion()
{

}

void EvaluatorDirectedLocomotion::Reset(double time)
{
  this->last_step_time = -this->evaluationRate_;
  this->step_poses.clear();
  Evaluator::Reset(time);
}

double EvaluatorDirectedLocomotion::Fitness()
{
  this->step_poses.push_back(this->currentPosition_);

  for (int i=0; i < this->step_poses.size(); i++)
  {
    const auto &pose = this->step_poses[i]; //[0,1,2,3,4,5,6,7,8]
    std::cout << "POSE[" << i << "]: " << pose << std::endl;
  }

  return Evaluator::Fitness();
  ////********** directed locomotion fitness function **********////
  //directions(forward) of heads are orientation(+x axis) - 1.570796
//  double beta0 = this->startPosition_.Rot().Yaw()-1.570796+0.698132;
//  //double beta0 = this->previousCurrent_.Rot().Yaw(); //for snakes./run
//  if (beta0 < - M_PI) //always less than pi (beta0 + max(40degree) < pi)
//  {
//    beta0 = 2 * M_PI - std::abs(beta0);
//  }
//
//  //save direction to coordinates.txt
//  std::ofstream coordinates;
//  coordinates.open("/Users/lan/projects/evert-simulator/tol-revolve"
//                       "/coordinates.txt", std::ios::app);
//  coordinates << std::fixed << "direction: " << beta0 << std::endl;
//
//  double beta1 = std::atan2(
//      this->currentPosition_.Pos().Y() - this->startPosition_.Pos().Y(),
//      this->currentPosition_.Pos().X() - this->startPosition_.Pos().X());
//
//  double alpha;
//  if (std::abs(beta1 - beta0) > M_PI)
//  {
//    alpha = 2 * M_PI - std::abs(beta1) - std::abs(beta0);
//  } else
//  {
//    alpha = std::abs(beta1 - beta0);
//  }
//  std::ofstream alphatxt;
//  alphatxt.open("/Users/lan/projects/evert-simulator/tol-revolve/alpha"
//                    ".txt", std::ios::app);
//  alphatxt << std::fixed << alpha << std::endl; //scientific notation
//
//  double A = std::tan(beta0);
//  double B = this->startPosition_.Pos().Y()
//             - A * this->startPosition_.Pos().X();
//
//  double X_p = (A * (this->currentPosition_.Pos().Y() - B)
//                + this->currentPosition_.Pos().X()) / (A * A + 1);
//  double Y_p = A * X_p + B;
//
//  //calculate the fitnessDirection based on distProjection, alpha, penalty
//  double distProjection;
//  double distPenalty;
//  double penalty;
//  double fitnessDirection;
//  double ksi = 1.0;
//  if (alpha > 0.5 * M_PI)
//  {
//    distProjection = -std::sqrt(
//        std::pow((this->startPosition_.Pos().X() - X_p), 2.0) +
//        std::pow((this->startPosition_.Pos().Y() - Y_p), 2.0));
//    distPenalty = std::sqrt(
//        std::pow((this->currentPosition_.Pos().X() - X_p), 2.0) +
//        std::pow((this->currentPosition_.Pos().Y() - Y_p), 2.0));
//    penalty = 0.01 * distPenalty;
//  } else
//  {
//    distProjection = std::sqrt(
//        std::pow((this->startPosition_.Pos().X() - X_p), 2.0) +
//        std::pow((this->startPosition_.Pos().Y() - Y_p), 2.0));
//    distPenalty = std::sqrt(
//        std::pow((this->currentPosition_.Pos().X() - X_p), 2.0) +
//        std::pow((this->currentPosition_.Pos().Y() - Y_p), 2.0));
//    penalty = 0.01 * distPenalty;
//  }
//
//  std::ofstream distPro;
//  distPro.open("/Users/lan/projects/evert-simulator/tol-revolve/distPro.txt", std::ios::app);
//  distPro << std::fixed << distProjection << std::endl; //scientific notation
//
//  //fitnessDirection = distProjection / (alpha + ksi) - penalty;
//
//  //-------------------------//
//  //        std::cout << "distPor = " << distProjection
//  //                  << " distPath = " << distPath
//  //                  << " alpha = " << alpha
//  //                  << " penalty = " << penalty << std::endl;
//  std::ofstream distPathTxt;
//  distPathTxt.open("/Users/lan/projects/evert-simulator/tol-revolve/distPath.txt", std::ios::app);
//  distPathTxt << std::fixed << lengthPath << std::endl;
//
//  fitnessDirection = std::abs(distProjection) / lengthPath *
//                     (distProjection / (alpha + ksi) - penalty);
//  //reset distP2P, distPath after a evaluation.
//  distP2P = 0.0;
//  lengthPath = 0.0;
//  //-------------------------//
//
//  std::ofstream fitness;
//  fitness.open("/Users/lan/projects/evert-simulator/tol-revolve/fitness.txt", std::ios::app);
//  fitness << std::fixed << fitnessDirection << std::endl; //scientific notation
//
//  fitnessDirection = 0.05 + fitnessDirection;
//  std::cout << std::fixed << "fitnessDirection : "
//            << fitnessDirection << std::endl;
//
//  return fitnessDirection;
}

void
EvaluatorDirectedLocomotion::Update(const ignition::math::Pose3d &_pose,
                                    const double time,
                                    const double step)
{
  this->previousPosition_ = currentPosition_;
  this->currentPosition_ = _pose;

  //If `last_step_time` is not initialized, do the initialization now
  if (this->last_step_time < 0)
  {
    this->last_step_time = time;
  }

  if ((time - this->last_step_time) > this->evaluationRate_ * this->step_saving_rate)
  {
    this->step_poses.push_back(_pose);
    this->last_step_time = time;
  };
}