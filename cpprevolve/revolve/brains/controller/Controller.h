//
// Created by matteo on 14/06/19.
//

#ifndef REVOLVE_CONTROLLER_H
#define REVOLVE_CONTROLLER_H

#include "actuators/Actuator.h"
#include "sensors/Sensor.h"
#include <vector>
#include <memory>

namespace revolve
{
class DifferentialCPG;

class Controller
{
public:
    enum ControllerType {
        NONE = 0,
        NEURAL_NETWORK,
        SPLINES,
        DIFFERENTIAL_CPG,
        RANDOM,
        // add new controller types here
    } const controller_type;

    /// \brief Constructor
    explicit Controller(ControllerType controller_type)
        : controller_type(controller_type)
    {}

    /// \brief Deconstructor
    virtual ~Controller() {}

    virtual void update(
            const std::vector<std::shared_ptr<Actuator>> &_actuators,
            const std::vector<std::shared_ptr<Sensor>> &_sensors,
            const double _time,
            const double _step
    ) = 0;

    virtual DifferentialCPG* into_DifferentialCPG() { return nullptr; }
};

}


#endif //REVOLVE_CONTROLLER_H
