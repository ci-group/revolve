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
 * Date: May 28, 2021
 *
 */
#ifndef REVOLVE_CELERYWORKER_H
#define REVOLVE_CELERYWORKER_H

#include <gazebo/gazebo.hh>
#include <gazebo/physics/physics.hh>
#include <gazebo/common/common.hh>
#include <gazebo/msgs/msgs.hh>
#include <SimpleAmqpClient/SimpleAmqpClient.h>
#include <json/json.h>
#include <boost/optional.hpp>
#include "database/Database.h"


namespace revolve::gazebo {

class CeleryWorker : public ::gazebo::WorldPlugin {
public:
    explicit CeleryWorker(std::string task_name);
    ~CeleryWorker() override;

    virtual void Load(
            ::gazebo::physics::WorldPtr _parent,
            sdf::ElementPtr _sdf) override;

    virtual void OnUpdateBegin(const ::gazebo::common::UpdateInfo &_info);
    virtual void OnUpdateEnd();

protected:
    void _check_for_messages(const ::gazebo::common::UpdateInfo &info);
    void _reply(const std::string &reply_to, const std::string &task_id, const std::string &correlation_id, Json::Value result);

    virtual void _simulator_work(const ::gazebo::common::UpdateInfo &info) = 0;
    virtual void _message_received(const ::gazebo::common::UpdateInfo &info, AmqpClient::Envelope::ptr_t envelope, const Json::Value &message_body) = 0;

protected:
    // RabbitMQ stuff
    const std::string TASK_NAME; // e.g. "pyrevolve.util.supervisor.rabbits.celery_queue.evaluate_robot";
    volatile std::atomic<bool> task_running = ATOMIC_FLAG_INIT;
    /// optional tuple containing < Robot name, robot model pointer (may be null), deadline >
    boost::optional<std::tuple<std::string, ::gazebo::physics::ModelPtr, double>> _task_robot;
    AmqpClient::Channel::ptr_t channel;
    std::string consumer_tag;
    Json::CharReaderBuilder readerBuilder;
    Json::StreamWriterBuilder writerBuilder;
    std::string _reply_to;
    std::string _correlation_id;
    std::string _task_id;

    // Postgresql stuff
    /// Update frequency for the robot states to be uploaded into the simulator
    unsigned int _robotStatesUpdateFreq = 0;
    double _lastRobotStatesUpdateTime = 0;
    std::string _dbname = "revolve";
    std::string _dbusername = "revolve";
    std::string _dbpassword = "revolve";
    std::string _dbaddress = "localhost";
    unsigned int _dbport = 5432;
    std::unique_ptr<Database> database = nullptr;
    unsigned int _database_robot_id = 0;
    unsigned int _evaluation_id = 1;

    // Gazebo stuff
    ::gazebo::physics::WorldPtr _world;
    std::string last_robot_analyzed;

    ::gazebo::physics::PhysicsEnginePtr _physics;
    // Pointer to the update event connection, keep here to keep alive
    ::gazebo::event::ConnectionPtr onBeginUpdateConnection;
    ::gazebo::event::ConnectionPtr onEndUpdateConnection;
};

}


#endif //REVOLVE_CELERYWORKER_H
