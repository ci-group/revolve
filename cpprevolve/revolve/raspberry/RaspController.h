//
// Created by matteo on 14/06/19.
//

#ifndef REVOLVE_RASPCONTROLLER_H
#define REVOLVE_RASPCONTROLLER_H

#include "../brains/controller/Controller.h"

namespace revolve {

class RaspController
        : public revolve::Controller
{
public:
    explicit RaspController();

    ~RaspController() override;

    void update(const std::vector<std::shared_ptr<Actuator> > &_actuators,
                const std::vector<std::shared_ptr<Sensor> > &_sensors, const double _time, const double _step) override;
};

}


#endif //REVOLVE_RASPCONTROLLER_H
