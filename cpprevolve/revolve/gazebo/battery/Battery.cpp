//
// Created by Roy Basmacier on 2019-07-09.
//

#include "Battery.h"

using namespace revolve::gazebo;

Battery::Battery(double initial_charge)
    : initial_charge(initial_charge), current_charge(initial_charge), watts_used(0)
    {}

void Battery::Update(double global_time, double delta_time)
{
    double sum = 0.0;
    //    std::cout << "battery: " << this->Voltage() << "V" << std::endl;
    for (const auto &consumer: this->PowerLoads()) {
//            std::cout << "comsumer: " << consumer.first << " -> " << consumer.second << std::endl;
        sum += consumer.second;
    }
    this->current_charge += sum * delta_time; // charge is measured in joules
    std::ofstream b_info_file;
    b_info_file.open("/Users/roy/projects/revolve/cpprevolve/revolve/gazebo/battery/battery_info_0.txt", std::ios_base::app);
    b_info_file << global_time << " " << sum << " " << current_charge << std::endl;
//    std::cout << this->watts_used<< std::endl;
}
