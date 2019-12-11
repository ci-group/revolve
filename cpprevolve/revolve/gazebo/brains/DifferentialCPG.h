//
// Created by andi on 20-09-19.
//

#pragma once

#include <revolve/brains/controller/actuators/Actuator.h>
#include <revolve/brains/controller/DifferentialCPG.h>
#include "Brain.h"

namespace revolve
{
    namespace gazebo
    {
        /// \brief connection between gazebo and revolve CPG
        /// \details gets the sdf - model data and passes them to revolve
        class DifferentialCPG: public Brain, public revolve::DifferentialCPG
        {
        public:
            /// \brief Constructor
            /// \param[in] brain_sdf ElementPtr containing the "brain" - tag of the model sdf
            /// \param[in] _motors vector<MotorPtr> list of motors
            /// \details Extracts controller parameters
            ///  from brain_sdf and calls revolve::DifferentialCPG's contructor.
            explicit DifferentialCPG(const sdf::ElementPtr brain_sdf,
                                     const std::vector< MotorPtr > &_motors);

            /// \brief updates the motor signals
            /// \param[in] _motors vector<MotorPtr> list of motors
            /// \param[in] _sensors vector<SensorPtr> list of sensors
            /// \param[in] _time double
            /// \param[in] _step double
            void Update(const std::vector<MotorPtr> &_motors,
                   const std::vector<SensorPtr> &_sensors,
                   const double _time,
                   const double _step) override;

        protected:
						explicit DifferentialCPG(const sdf::ElementPtr brain_sdf,
                                                 const std::vector<MotorPtr> &_motors,
                                                 const NEAT::Genome &genome);

            /// \brief extracts CPG controller parameters from brain_sdf
            /// \param[in] brain_sdf ElementPtr containing the "brain" - tag of the model sdf
            /// \return parameters of the CPG controller
            /// \details get the strings of the controller parameters and convert them to the
            /// appropriate datatype. Store them in a revolve::DifferentialCPG::ControllerParams
            /// struct and return them.
            static revolve::DifferentialCPG::ControllerParams load_params_from_sdf(sdf::ElementPtr brain_sdf);
        };
    }
}
