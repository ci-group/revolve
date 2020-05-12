//
// Created by andi on 11-10-19.
//

#ifndef REVOLVE_DIFFERENTIALCPPNCPG_H
#define REVOLVE_DIFFERENTIALCPPNCPG_H

#include <revolve/brains/controller/actuators/Actuator.h>
#include "DifferentialCPG.h"
#include "Brain.h"


namespace revolve {
    namespace gazebo {

        /// \brief connection between gazebo and revolve CPG with config CPPN
        /// \details gets the sdf - model data and passes them to revolve
        class DifferentialCPPNCPG : public DifferentialCPG
				{
        public:
            /// \brief Constructor
            /// \param[in] brain_sdf ElementPtr containing the "brain" - tag of the model sdf
            /// \param[in] _motors vector<MotorPtr> list of motors
            /// \details Extracts controller parameters and Genome
            ///  from brain_sdf and calls revolve::DifferentialCPG's contructor.
            explicit DifferentialCPPNCPG(const sdf::ElementPtr brain_sdf,
                                          const std::vector< MotorPtr > &_motors);

				protected:
						static NEAT::Genome load_cppn_genome_from_sdf(const sdf::ElementPtr brain_sdf);
        };
    }
}


#endif //REVOLVE_DIFFERENTIALCPPNCPG_H
