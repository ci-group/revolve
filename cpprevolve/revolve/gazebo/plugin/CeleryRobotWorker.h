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
 * Date: Jun 03, 2021
 *
 */
#ifndef REVOLVE_CELERYROBOTWORKER_H
#define REVOLVE_CELERYROBOTWORKER_H

#include <gazebo/gazebo.hh>
#include <gazebo/physics/physics.hh>
#include "CeleryWorker.h"

namespace revolve::gazebo {

class CeleryRobotWorker : public CeleryWorker {
public:
    CeleryRobotWorker();
    ~CeleryRobotWorker() override;

    virtual void Load(
            ::gazebo::physics::WorldPtr _parent,
            sdf::ElementPtr _sdf) override;

protected:
    void _simulator_work(const ::gazebo::common::UpdateInfo &info) override;
    void _message_received(const ::gazebo::common::UpdateInfo &info, AmqpClient::Envelope::ptr_t envelope, const Json::Value &message_body) override;
    bool _robot_work(const ::gazebo::common::UpdateInfo &info);
    void _saveRobotState(const ::gazebo::common::UpdateInfo &info);
};

}

#endif //REVOLVE_CELERYROBOTWORKER_H
