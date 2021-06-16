/*
* Copyright (C) 2017 Vrije Universiteit Amsterdam
*
* Licensed under the Apache License, Version 2.0 (the "License");
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
* Author: Elte Hupkes
* Date: Mar 5, 2015
*
*/

#include <string>

#include <revolve/gazebo/motors/Motor.h>
#include <boost/algorithm/string.hpp>

namespace gz = gazebo;

using namespace revolve::gazebo;

/////////////////////////////////////////////////
::revolve::gazebo::Motor::Motor (
    ::gazebo::physics::ModelPtr _model,
    const std::string &_partId,
    const std::string &_motorId,
    const unsigned int outputNeurons,
    const std::string &_coordinates)
    : revolve::Actuator(outputNeurons, 0, 0, 0)
    , model_(std::move(_model))
    , partId_(_partId)
    , motorId_(_motorId)
{
    // TODO conversion crashes if coordinates string is empty
    std::vector<std::string> coordinates;
    double d_coordinates[3] = {0,0,0};

    boost::split(coordinates, _coordinates, boost::is_any_of(";"));

    for(int i=0; i<coordinates.size(); i++)
    {
        d_coordinates[i] = std::stod(coordinates[i]);
    }

    this->coordinates = std::tuple<double, double, double>{d_coordinates[0], d_coordinates[1], d_coordinates[2]};
}

/////////////////////////////////////////////////
Motor::~Motor() = default;

/////////////////////////////////////////////////
std::string Motor::PartId()
{
  return this->partId_;
}

/////////////////////////////////////////////////
unsigned int Motor::Outputs()
{
  return this->n_outputs();
}

/////////////////////////////////////////////////
gz::common::PID Motor::CreatePid(sdf::ElementPtr _sdfPID)
{
  auto pv = 0.0;
  auto iv = 0.0;
  auto dv = 0.0;
  auto iMax = 0.0;
  auto iMin = 0.0;
  auto cmdMax = 1.0;
  auto cmdMin = -1.0;

  if (_sdfPID->HasElement("rv:p"))
  {
    pv = _sdfPID->GetElement("rv:p")->Get< double >();
  }
  if (_sdfPID->HasElement("rv:i"))
  {
    iv = _sdfPID->GetElement("rv:i")->Get< double >();
  }
  if (_sdfPID->HasElement("rv:d"))
  {
    dv = _sdfPID->GetElement("rv:d")->Get< double >();
  }
  if (_sdfPID->HasElement("rv:i_max"))
  {
    iMax = _sdfPID->GetElement("rv:i_max")->Get< double >();
  }
  if (_sdfPID->HasElement("rv:i_min"))
  {
    iMin = _sdfPID->GetElement("rv:i_min")->Get< double >();
  }
  if (_sdfPID->HasElement("rv:cmd_max"))
  {
    cmdMax = _sdfPID->GetElement("rv:cmd_max")->Get< double >();
  }
  if (_sdfPID->HasElement("rv:cmd_min"))
  {
    cmdMin = _sdfPID->GetElement("rv:cmd_min")->Get< double >();
  }

  return gz::common::PID(pv, iv, dv, iMax, iMin, cmdMax, cmdMin);
}

/////////////////////////////////////////////////
std::string Motor::MotorId()
{
  return this->motorId_;
}
