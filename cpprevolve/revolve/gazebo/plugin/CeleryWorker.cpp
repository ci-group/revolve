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
#include <cassert>
#include <gazebo/common/Events.hh>
#include <gazebo/gazebo.hh>
#include <gazebo/physics/physics.hh>
#include <gazebo/common/common.hh>
#include <gazebo/msgs/msgs.hh>
#include "CeleryWorker.h"

using namespace revolve::gazebo;

void print_table_value(const AmqpClient::TableValue &value);

CeleryWorker::CeleryWorker()
    : _world(nullptr)
    , _physics(nullptr)
{
    _task_robot.reset();
    writerBuilder.settings_["indentation"] = "";
}

CeleryWorker::~CeleryWorker() = default;

template <typename T>
T getAttribute(const sdf::ElementPtr &_elem, const std::string &_key, const T& _default) {
    sdf::ParamPtr attribute = _elem->GetAttribute(_key);
    if (attribute == nullptr) {
        return _default;
    }
    T value;
    bool conversion_successful = attribute->Get<T>(value);
    if (conversion_successful) {
        return value;
    } else {
        return _default;
    }
}

template <>
std::string getAttribute<std::string>(const sdf::ElementPtr &_elem, const std::string &_key, const std::string& _default) {
    sdf::ParamPtr attribute = _elem->GetAttribute(_key);
    if (attribute == nullptr) {
        return _default;
    }
    std::string value = attribute->GetAsString();
    if (value.empty()) {
        return _default;
    } else {
        return value;
    }
}

void CeleryWorker::Load(::gazebo::physics::WorldPtr world, sdf::ElementPtr sdf)
{
    this->_world = world;
    _physics = world->Physics();
    assert(_physics != nullptr);

    if (sdf->HasElement("rv:database")) {
        const sdf::ElementPtr SDF_database = sdf->GetElement("rv:database");
        this->_dbname = getAttribute<std::string>(SDF_database, "dbname", "revolve");
        this->_dbusername = getAttribute<std::string>(SDF_database, "username", "revolve");
        this->_dbpassword = getAttribute<std::string>(SDF_database, "password", "revolve");
        this->_dbaddress = getAttribute<std::string>(SDF_database, "address", "localhost");
        this->_dbport = getAttribute<unsigned int>(SDF_database, "port", 5432);
    }

    // Turn on threading
//    physicsEngine->SetParam("thread_position_correlation", true);
//    physicsEngine->SetParam("island_threads", 8);

    //TODO read this value from the world SDF file
    this->_robotStatesUpdateFreq = 5;


    // Bind to the world update event to perform some logic
    this->onBeginUpdateConnection = ::gazebo::event::Events::ConnectWorldUpdateBegin(
            [this] (const ::gazebo::common::UpdateInfo &_info) {this->OnUpdateBegin(_info);});
    this->onEndUpdateConnection = ::gazebo::event::Events::ConnectWorldUpdateEnd(
            [this] () {this->OnUpdateEnd();});

    // Create a connection to RabbitMQ
    AmqpClient::Channel::OpenOpts options;
    options.host = "localhost";
    options.auth = AmqpClient::Channel::OpenOpts::BasicAuth("guest", "guest");
    channel = AmqpClient::Channel::Open(options);

    consumer_tag = channel->BasicConsume(
            "celery",
            "", // empty string, the library will generate this for us
            true,
            false, // acknowledge manually
            false, // allow other workers
            1 // no buffering
    );
    std::cout << "Started Gazebo worker with tag: " << consumer_tag << std::endl;

    // Connection to the database
    database = std::make_unique<Database>(_dbname, _dbusername, _dbpassword, _dbaddress, _dbport);
}

void CeleryWorker::OnUpdateBegin(const ::gazebo::common::UpdateInfo &info)
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
    this->_check_for_messages(info);
}

bool CeleryWorker::_robot_work(const ::gazebo::common::UpdateInfo &info)
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

void CeleryWorker::_saveRobotState(const ::gazebo::common::UpdateInfo &info)
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

void CeleryWorker::OnUpdateEnd()
{
}

void CeleryWorker::_check_for_messages(const ::gazebo::common::UpdateInfo &info)
{
    //TODO improve performance by choosing the correct memory order
    if (task_running.load(std::memory_order_seq_cst)) {
        // A task is already running, do not check for new tasks
        return;
    }

    if (_world->ModelByName(this->last_robot_analyzed) != nullptr) {
        // A robot is not running, but the model is still present in the
        // data structure of the simulator, we wait that gazebo re-syncs before
        // inserting a new one. Because high-quality unnecessarely network-based Gazebo.
        std::cout << "Cleaning up from previous robot" << std::endl;
        return;
    }

    // std::cout << "Checking for celery task" << std::endl;
    AmqpClient::Envelope::ptr_t envelope;
    auto message_received = channel->BasicConsumeMessage(
            consumer_tag,
            envelope,
            1000);
    if (!message_received) {
        return; // no message
    }

    task_running.store(true, std::memory_order_seq_cst);
    auto message = envelope->Message();
    _reply_to = message->ReplyTo();
    _correlation_id = message->CorrelationId();

    const std::string task_name = message->HeaderTable().at("task").GetString();
    //TODO set task name from SDF
    if (task_name != this->TASK_NAME) {
        channel->BasicAck(envelope);
        channel->BasicReject(envelope, true);
        task_running.store(false, std::memory_order_seq_cst);
        return;
    }

    const std::string &body_string = message->Body();
    std::cout << "Received task: \"" << task_name << '"' << std::endl;
    // Prints the header table of the message that arrived
//    for (auto &i : message->HeaderTable()) {
//        std::cout << i.first << ":";
//        print_table_value(i.second);
//        std::cout << std::endl;
//    }
    Json::Value body;
    JSONCPP_STRING err;
    const std::unique_ptr<Json::CharReader> reader(readerBuilder.newCharReader());
    const char *start = body_string.c_str();
    const char *end = start + body_string.length() -1;
    bool error = reader->parse(start, end, &body, &err);
    if (error) {
        std::cerr << "error parsing json" << err << std::endl;
        channel->BasicReject(envelope, false);
        //channel->BasicCancel(consumer_tag);
        task_running.store(false, std::memory_order_seq_cst);
        return; //error
    }

    // Parse JSON REQUEST
    _task_id = message->HeaderTable().at("id").GetString();

    std::cout << "working on task: " << _task_id << std::endl;

    //extract the robot SDF and the robot lifetime from the request
    //    @app.task
    //    def evaluate_robot(robot_sdf: AnyStr, life_timeout: float):
    Json::Value params;
    const char * SDFtext;
    double lifetime;
    try {
        params = body[0];
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
    channel->BasicAck(envelope);


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
        channel->BasicReject(envelope, false);
    }

    // Don't leak memory
    // https://bitbucket.org/osrf/sdformat/issues/104/memory-leak-in-element
    //robotSDF.Root()->Reset();
}

void CeleryWorker::_reply(const std::string &reply_to, const std::string &task_id, const std::string &correlation_id, Json::Value result) {
    const std::string &routing_key = reply_to;
    const char *state = "SUCCESS";

    Json::Value msg;
    msg["task_id"] = task_id;
    msg["status"] = state;
    msg["result"] = std::move(result);
    msg["traceback"] = Json::Value::null;
    msg["children"] = Json::Value(Json::ValueType::arrayValue);

    const std::string serialized = Json::writeString(writerBuilder, msg);
    const std::string serialized2 = Json::writeString(writerBuilder, msg);

    auto return_msg = AmqpClient::BasicMessage::Create(serialized);
    return_msg->ContentType("application/json");
    return_msg->ContentEncoding("utf-8");
    return_msg->CorrelationId(correlation_id);
    return_msg->HeaderTable({
                             {"id", task_id },
                             {"task", TASK_NAME }
                     });

    channel->BasicPublish("", routing_key, return_msg);
}


void print_table_value(const AmqpClient::TableValue &value) {
    switch (value.GetType()) {
        case AmqpClient::TableValue::VT_array:
            std::cout << '[';
            for (auto const &elem : value.GetArray()) {
                print_table_value(elem);
                std::cout << ',';
            }
            std::cout << ']';
            break;
        case AmqpClient::TableValue::VT_bool:
            std::cout << (value.GetBool() ? "true" : "false");
            break;
        case AmqpClient::TableValue::VT_double:
        case AmqpClient::TableValue::VT_float:
            std::cout << value.GetReal();
            break;
        case AmqpClient::TableValue::VT_string:
            std::cout << '"' << value.GetString() << '"';
            break;
        case AmqpClient::TableValue::VT_table:
            std::cout << '{';
            for (auto const &v : value.GetTable()) {
                std::cout << v.first << ':';
                print_table_value(v.second);
            }
            std::cout << '}';
            break;
        case AmqpClient::TableValue::VT_timestamp:
            std::cout << value.GetTimestamp();
            break;
        case AmqpClient::TableValue::VT_int16:
        case AmqpClient::TableValue::VT_int32:
        case AmqpClient::TableValue::VT_int64:
        case AmqpClient::TableValue::VT_int8:
        case AmqpClient::TableValue::VT_uint16:
        case AmqpClient::TableValue::VT_uint32:
        case AmqpClient::TableValue::VT_uint8:
            std::cout << value.GetInteger();
            break;
        case AmqpClient::TableValue::VT_void:
            std::cout << "null";
            break;
        default:
            throw std::runtime_error("Invalid `AmqpClient::TableValue` value" + std::to_string(value.GetType()));
    }
}
