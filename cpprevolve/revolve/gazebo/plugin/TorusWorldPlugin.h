/*
* Copyright (C) 2021 Vrije Universiteit Amsterdam
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
* Author: Matteo De Carlo
*
*/

#ifndef REVOLVE_TORUSWORLDPLUGIN_H
#define REVOLVE_TORUSWORLDPLUGIN_H

#include <gazebo/gazebo.hh>
#include <gazebo/physics/physics.hh>

namespace revolve {
namespace gazebo {

class TorusWorldPlugin : public ::gazebo::WorldPlugin {
protected:

    double margin_px;
    double margin_nx;
    double margin_py;
    double margin_ny;

    // Stores the world
    ::gazebo::physics::WorldPtr world_;

    // Pointer to the update event connection
    ::gazebo::event::ConnectionPtr onBeginUpdateConnection;

public:
    TorusWorldPlugin();

    ~TorusWorldPlugin() override = default;

    void Load(
            ::gazebo::physics::WorldPtr _parent,
            sdf::ElementPtr sdf
            ) override;

    void Reset() override;

    void SetMargins(const ::ignition::math::Vector2d &center, double size_x, double size_y);
    void SetMargins(double margin_px_, double margin_nx, double margin_py_, double margin_ny_);

protected:
    void OnBeginUpdate(const ::gazebo::common::UpdateInfo &_info);
};

}
}

#endif //REVOLVE_TORUSWORLDPLUGIN_H
