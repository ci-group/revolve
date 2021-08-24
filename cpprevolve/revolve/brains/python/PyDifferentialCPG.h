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
#ifndef REVOLVE_PYDIFFERENTIALCPG_H
#define REVOLVE_PYDIFFERENTIALCPG_H


#include "../controller/DifferentialCPG.h"

class PyDifferentialCPG : public ::revolve::DifferentialCPG
{
public:
    PyDifferentialCPG(::revolve::DifferentialCPG::ControllerParams params, std::vector<std::shared_ptr<::revolve::Actuator>> actuators);
    ~PyDifferentialCPG() override = default;
};


#endif //REVOLVE_PYDIFFERENTIALCPG_H
