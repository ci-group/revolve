//
// Created by Roy Basmacier on 2019-07-09.
//

#ifndef REVOLVE_BATTERY_H
#define REVOLVE_BATTERY_H


#include <gazebo/gazebo.hh>
#include <gazebo/physics/physics.hh>
#include <gazebo/common/common.hh>
#include <gazebo/msgs/msgs.hh>

#include <revolve/gazebo/Types.h>

namespace revolve{
namespace gazebo{

class Battery : public ::gazebo::common::Battery
{
public:
    explicit Battery(double initial_charge);

    void Update(double global_time, double delta_time);

protected:
    /// \brief initial charge of the battery in joules
    double initial_charge; // it is set in RobotController.cpp

    /// \brief current charge of the battery in joules
    double current_charge;

    /// \brief the time of initiation (for creating data files of battery delete later)
    std::string time_init;

    std::string robot_name;

    friend class RobotController;
    friend class Evaluator;
    friend class DifferentialCPG;
};

}
}

#endif //REVOLVE_BATTERY_H
