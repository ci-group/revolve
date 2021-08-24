/*
 * Copyright (C) 2015-2021 Vrije Universiteit Amsterdam
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
 * Author: Matteo De Carlo
 * Date: Aug 2, 2021
 *
 */
#include "PyActuator.h"
#include "PySensor.h"
#include "PyController.h"
#include "../controller/FixedAngleController.h"
#include "PyDifferentialCPG.h"

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;

int add(int i = 1, int j = 2) {
    return i + j;
}

namespace revolve {
    class DifferentialCPG;
}

PYBIND11_MODULE(revolvebrains, m) {
    using namespace revolve;
    m.doc() = "Revolve Brains: controllers and learners";

    m.def("add", &add, "A function which adds two numbers",
          py::arg("i"), py::arg("j"));
    
    py::class_<Actuator, PyActuator, std::shared_ptr<Actuator>>(m, "Actuator")
            .def(py::init<unsigned int, double, double, double>())
            .def(py::init<unsigned int, std::tuple<double, double, double>>())
            .def_property_readonly("x", &Actuator::coordinate_x)
            .def_property_readonly("y", &Actuator::coordinate_y)
            .def_property_readonly("z", &Actuator::coordinate_z)
            .def("n_outputs", &Actuator::n_outputs)
            .def("__len__", &Actuator::n_outputs)
            .def("write", &Actuator::write)
    ;

    py::class_<Sensor, PySensor, std::shared_ptr<Sensor>>(m, "Sensor")
            .def(py::init<unsigned int>())
            .def("n_inputs", &Sensor::n_inputs, "Number of inputs that the sensor is providing")
            .def("__len__", &Sensor::n_inputs, "Number of inputs that the sensor is providing")
            .def("read", &Sensor::read, "Read the value of the sensor into the input array")
    ;

    py::class_<Controller, PyController>(m, "Controller")
            .def(py::init())
            .def("update", &Controller::update,
                 "The default update method for the controller",
                 py::arg("actuators"),
                 py::arg("sensors"),
                 py::arg("time"),
                 py::arg("step"))
    ;

    py::class_<FixedAngleController>(m, "FixedAngleController")
            .def(py::init<double>())
            .def("update", &FixedAngleController::update)
    ;

    py::class_<DifferentialCPG::ControllerParams>(m, "DifferentialCPG_ControllerParams")
            .def(py::init())
            .def_readwrite("reset_neuron_random", &DifferentialCPG::ControllerParams::reset_neuron_random)
            .def_readwrite("use_frame_of_reference", &DifferentialCPG::ControllerParams::use_frame_of_reference)
            .def_readwrite("init_neuron_state", &DifferentialCPG::ControllerParams::init_neuron_state)
            .def_readwrite("range_ub", &DifferentialCPG::ControllerParams::range_ub)
            .def_readwrite("signal_factor_all", &DifferentialCPG::ControllerParams::signal_factor_all)
            .def_readwrite("signal_factor_mid", &DifferentialCPG::ControllerParams::signal_factor_mid)
            .def_readwrite("signal_factor_left_right", &DifferentialCPG::ControllerParams::signal_factor_left_right)
            .def_readwrite("abs_output_bound", &DifferentialCPG::ControllerParams::abs_output_bound)
            .def_readwrite("weights", &DifferentialCPG::ControllerParams::weights)
            .def("__repr__", [](const DifferentialCPG::ControllerParams& c) {
                std::ostringstream repr;
                repr << "<revolvebrains.CPG_ControllerParams at " << &c << std::endl
                     << "\treset_neuron_random      = " << (c.reset_neuron_random    ? "True" : "False") << std::endl
                     << "\tuse_frame_of_reference   = " << (c.use_frame_of_reference ? "True" : "False") << std::endl
                     << "\tinit_neuron_state        = " << c.init_neuron_state        << std::endl
                     << "\trange_ub                 = " << c.range_ub                 << std::endl
                     << "\tsignal_factor_all        = " << c.signal_factor_all        << std::endl
                     << "\tsignal_factor_mid        = " << c.signal_factor_mid        << std::endl
                     << "\tsignal_factor_left_right = " << c.signal_factor_left_right << std::endl
                     << "\tabs_output_bound         = " << c.abs_output_bound         << std::endl
                     << "\tweights                  = [";
                for (auto it = c.weights.begin(); it != c.weights.end(); ++it) {
                    repr << *it;
                    if (it+1 != c.weights.end()) {
                        repr << ';';
                    }
                }
                repr << "] >";
                return repr.str();
            })
    ;

    py::class_<revolve::DifferentialCPG, PyDifferentialCPG>(m, "DifferentialCPG")
            .def(py::init<DifferentialCPG::ControllerParams, std::vector<std::shared_ptr<Actuator>>>())
//            .def(py::init<DifferentialCPG::ControllerParams, std::vector<std::shared_ptr<Actuator>>, NEAT::Genome>())
            .def("update", &DifferentialCPG::update,
                 "The default update method for the controller",
                 py::arg("actuators"),
                 py::arg("sensors"),
                 py::arg("time"),
                 py::arg("step"))
    ;
}
