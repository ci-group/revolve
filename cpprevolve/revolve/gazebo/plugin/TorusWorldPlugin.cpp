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

#include "TorusWorldPlugin.h"
#include <string>

namespace gz = ::gazebo;
using namespace revolve::gazebo;

TorusWorldPlugin::TorusWorldPlugin()
        : margin_px(0.0)
          , margin_nx(0.0)
          , margin_py(0.0)
          , margin_ny(0.0)
{
    SetMargins(ignition::math::Vector2d(0, 0), 10, 10);
}

void TorusWorldPlugin::Load(gz::physics::WorldPtr world, const sdf::ElementPtr sdf)
{
    this->world_ = world;

    // Default box size and position
    ignition::math::Vector2d center(0, 0);
    double size_x = 10.0;
    double size_y = 10.0;

    if (sdf->HasElement("area")) {
        const sdf::ElementPtr areaSDF = sdf->GetElement("area");
        assert(areaSDF != nullptr);

        // Load Box size and position from SDF, if provided
        try {
            if (areaSDF->HasAttribute("center_x") && areaSDF->HasAttribute("center_y")) {
                center.X(std::stod(areaSDF->GetAttribute("center_x")->GetAsString()));
                center.Y(std::stod(areaSDF->GetAttribute("center_y")->GetAsString()));
            }
        } catch (const std::exception &e) {
            std::cerr << "Could not load center from the SDF; error: " << e.what() << std::endl;
        }

        try {
            if (areaSDF->HasAttribute("size_x"))
            { size_x = std::stod(areaSDF->GetAttribute("size_x")->GetAsString()); }
        } catch (const std::exception &e) {
            std::cerr << "Could not load size_x from the SDF; error: " << e.what() << std::endl;
        }

        try {
            if (areaSDF->HasAttribute("size_y"))
            { size_y = std::stod(areaSDF->GetAttribute("size_y")->GetAsString()); }
        } catch (const std::exception &e) {
            std::cerr << "Could not load size_y from the SDF; error: " << e.what() << std::endl;
        }

    }

    // Set box size and position
    SetMargins(center, size_x, size_y);

    // Bind to the world update event to perform some logic
    this->onBeginUpdateConnection = gz::event::Events::ConnectWorldUpdateBegin(
            [this](const ::gazebo::common::UpdateInfo &_info) { this->OnBeginUpdate(_info); });

    std::cout << "Torus World plugin loaded;" << std::endl;
}

void TorusWorldPlugin::Reset()
{}

void TorusWorldPlugin::SetMargins(const ::ignition::math::Vector2d &center, double size_x, double size_y)
{
    double margin_px_ = center.X() + size_x / 2.0;
    double margin_nx_ = center.X() - size_x / 2.0;
    double margin_py_ = center.Y() + size_y / 2.0;
    double margin_ny_ = center.Y() - size_y / 2.0;
    this->SetMargins(margin_px_, margin_nx_, margin_py_, margin_ny_);
}

void TorusWorldPlugin::SetMargins(double margin_px_, double margin_nx_, double margin_py_, double margin_ny_)
{
    this->margin_px = margin_px_;
    this->margin_nx = margin_nx_;
    this->margin_py = margin_py_;
    this->margin_ny = margin_ny_;
    std::cout << "Torus World plugin, new margins: x[" << margin_nx_ << ';' << margin_px_ << "] y[" << margin_ny_ << ';' << margin_py_ << "]" << std::endl;
}

void TorusWorldPlugin::OnBeginUpdate(const gz::common::UpdateInfo &_info)
{
    boost::recursive_mutex::scoped_lock lock_physics(*this->world_->Physics()->GetPhysicsUpdateMutex());
    for (const boost::shared_ptr<gz::physics::Model> &model : this->world_->Models()) {
        if (model->IsStatic()) {
            // Ignore static models such as the ground and obstacles
            continue;
        }

        bool changed = false;

        ignition::math::Pose3d pose = model->WorldPose();
        ignition::math::Vector3d &pos = pose.Pos();
        if (pos.X() > margin_px) {
            pos.X(margin_nx);
            changed = true;
        } else if (pos.X() < margin_nx) {
            pos.X(margin_px);
            changed = true;
        }

        if (pos.Y() > margin_py) {
            pos.Y(margin_ny);
            changed = true;
        } else if (pos.Y() < margin_ny) {
            pos.Y(margin_py);
            changed = true;
        }

        if (changed) {
            model->SetWorldPose(pose);
        }
    }
}