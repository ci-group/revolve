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
#include "CeleryRobotWorker.h"

using namespace revolve::gazebo;

CeleryRobotWorker::CeleryRobotWorker()
    : CeleryWorker("pyrevolve.util.supervisor.rabbits.celery_queue.evaluate_robot")
{

}

CeleryRobotWorker::~CeleryRobotWorker() = default;


void CeleryRobotWorker::Load(::gazebo::physics::WorldPtr _parent, sdf::ElementPtr _sdf) {
    CeleryWorker::Load(_parent, _sdf);
}

void CeleryRobotWorker::_simulator_work(const ::gazebo::common::UpdateInfo &info)
{
    // here we know what time is it in the simulator
    bool alive = this->_robot_work(info);
    if (alive) {
        // Update the DB only if the robot is alive.
        // Sometimes it can enter in a ghost state because it's already dead
        // but we haven't received a valid pointer to the model yet.
        // Which speaks lots for the quality of gazebo
        this->_saveRobotState(info);
    }
}

bool CeleryRobotWorker::_robot_work(const ::gazebo::common::UpdateInfo &info)
{
    if (not task_running.load(std::memory_order_seq_cst)) {
        // A task is not running, there is no robot work to do
        return false;
    }

    assert(_task_robot.has_value());
    std::tuple<std::string, ::gazebo::physics::ModelPtr, double> &tuple_task = _task_robot.value();
    const std::string &name = std::get<0>(tuple_task);
    ::gazebo::physics::ModelPtr &robot_model = std::get<1>(tuple_task);
    double death_sentence = std::get<2>(tuple_task);

    if (not robot_model) {
        ::gazebo::physics::ModelPtr model = _world->ModelByName(name);
        if (model) {
            std::cout << "Model added, pointer is " << model.get() << std::endl;
            std::cout << "\tname: " << model->GetName() << std::endl;
        } else {
//            std::clog << "ADDED MODEL DOES NOT HAVE A POINTER!" << std::endl;
        }
        robot_model.swap(model);
    }

    double time = info.simTime.Double();
    bool alive = death_sentence > time;

    if (not alive) {
        // The robot just died, let's finish the task

        // remove model
        ::gazebo::physics::ModelPtr model = std::get<1>(*_task_robot);
        if (model) {
            this->_world->RemoveModel(model);
        } else {
//            std::cerr << "Cannot remove robot, model pointer not valid!" << std::endl;
            return false;
        }

        std::cout << "Robot evaluation finished: " << std::get<0>(*_task_robot) << std::endl;
        this->_reply(_reply_to, _task_id, _correlation_id, _database_robot_id);
        _reply_to.resize(0);
        _task_id.resize(0);
        _task_robot.reset();
        last_robot_analyzed = name;
        task_running.store(false, std::memory_order_seq_cst);
    }

    return alive;
}

void CeleryRobotWorker::_saveRobotState(const ::gazebo::common::UpdateInfo &info)
{
    if (not this->_robotStatesUpdateFreq) return;

    double secs = 1.0 / _robotStatesUpdateFreq;
    double time = info.simTime.Double();
    if ((time - this->_lastRobotStatesUpdateTime) >= secs) {
        database->start_state_work();
        // collect data of the current time step
        {
            boost::recursive_mutex::scoped_lock lock_physics(*_physics->GetPhysicsUpdateMutex());
            for (const boost::shared_ptr<::gazebo::physics::Model> &model : this->_world->Models()) {
                if (model->IsStatic()) {
                    // Ignore static models such as the ground and obstacles
                    continue;
                }

                auto id = model->GetId();
                auto pose = model->WorldPose();
                //TODO orientation vectors
                const std::string &name = model->GetName();

                database->add_state(_database_robot_id, _evaluation_id, time, pose);
            }
        }
        //TODO buffer the states data in less postgres commands to increase performance
        // at the cost of a few seconds of data loss
        database->commit_state_work();

        _lastRobotStatesUpdateTime = time;
    }
}

void CeleryRobotWorker::_message_received(const ::gazebo::common::UpdateInfo &info, AmqpClient::Envelope::ptr_t envelope, const Json::Value &message_body)
{
    //extract the robot SDF and the robot lifetime from the request
    //    @app.task
    //    def evaluate_robot(robot_sdf: AnyStr, life_timeout: float):
    Json::Value params;
    const char * SDFtext;
    double lifetime;
    try {
        params = message_body[0];
        SDFtext = params[0].asCString();
        lifetime = params[1].asDouble();
    } catch (const Json::LogicError &e) {
        // reject and remove task from the queue
        channel->BasicAck(envelope);
        channel->BasicReject(envelope, false);
        std::cerr << "Error parsing json for incoming task: " << std::endl
                  << e.what() << std::endl;
        task_running.store(false, std::memory_order_seq_cst);
        return;
    }


    // Insert the robot in the simulation
    sdf::SDF robotSDF;
    robotSDF.SetFromString(SDFtext);
    std::string name = robotSDF.Root()->GetElement("model")->GetAttribute("name")
            ->GetAsString();
    if (name == last_robot_analyzed) {
        // TODO handle this better, this does not work and locks the simulator!
        std::chrono::milliseconds twoseconds(100);
        std::this_thread::sleep_for(twoseconds);
        if (_world->ModelByName(name)) {
            channel->BasicAck(envelope);
            channel->BasicReject(envelope, true);
            std::cerr << "Inserting the previous robot immediately could cause problems in the simulation." << std::endl
                      << "Rejecting the task and sending it to the next worker" << std::endl;
            task_running.store(false, std::memory_order_seq_cst);
            return;
        }
    }

    //_world->InsertModelString(SDFtext)
    _world->InsertModelSDF(robotSDF);

    double deadline = info.simTime.Double() + lifetime;
    _task_robot = std::make_tuple(name, nullptr, deadline);

    try {
        _database_robot_id = database->add_or_get_robot(name);
        database->add_or_recreate_evaluation(_database_robot_id, _evaluation_id, -1);
    } catch (const std::runtime_error& e) {
        // TODO handle this better, replace the last run with this one.
        std::cerr << "Error adding robot " << name << " to the Database: " << e.what() << std::endl;
        channel->BasicAck(envelope);
        channel->BasicReject(envelope, false);
    }

    // Don't leak memory
    // https://bitbucket.org/osrf/sdformat/issues/104/memory-leak-in-element
    //robotSDF.Root()->Reset();

    //TODO move the Ack to when the robot is finished working
    channel->BasicAck(envelope);
}
