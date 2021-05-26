//
// Created by matteo on 6/19/19.
//

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

CeleryWorker::~CeleryWorker()
{

}

void CeleryWorker::Load(::gazebo::physics::WorldPtr world, sdf::ElementPtr sdf)
{
    this->_world = world;
    _physics = world->Physics();
    assert(_physics != nullptr);

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
    database = std::make_unique<Database>("pythoncpptest");
}

void CeleryWorker::OnUpdateBegin(const ::gazebo::common::UpdateInfo &info)
{
    // here we know what time is it in the simulator
    this->_robot_work(info);
    this->_saveRobotState(info);
    this->_check_for_messages(info);
}

void CeleryWorker::_robot_work(const ::gazebo::common::UpdateInfo &info)
{
    if (not task_running.load(std::memory_order_seq_cst)) {
        // A task is already running, do not check for new tasks
        return;
    }

    assert(_task_robot.has_value());
    std::tuple<std::string, ::gazebo::physics::ModelPtr, double> &tuple_task = _task_robot.value();
    const std::string &name = std::get<0>(tuple_task);
    ::gazebo::physics::ModelPtr &robot_model = std::get<1>(tuple_task);
    double death_sentence = std::get<2>(tuple_task);

    if (not robot_model) {
        ::gazebo::physics::ModelPtr model = _world->ModelByName(name);
        std::cout << "Model added, pointer is " << model.get() << std::endl;
        if (model) {
            std::cout << "\tname: " << model->GetName() << std::endl;
        } else {
            std::clog << "ADDED MODEL DOES NOT HAVE A POINTER!" << std::endl;
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
            std::cerr << "Cannot remove robot, model pointer not valid!" << std::endl;
            return;
        }

        double fitness = rand();

        std::cout << "Robot evaluation finished with fitness: " << fitness << std::endl;
        this->_reply(_reply_to, _task_id, _database_robot_id);
        _reply_to.resize(0);
        _task_id.resize(0);
        _task_robot.reset();
        last_robot_analyzed = name;
        task_running.store(false, std::memory_order_seq_cst);
    }
}

void CeleryWorker::_saveRobotState(const ::gazebo::common::UpdateInfo &info)
{
    if (not this->_robotStatesUpdateFreq) return;

    double secs = 1.0 / _robotStatesUpdateFreq;
    double time = info.simTime.Double();
    if ((time - this->_lastRobotStatesUpdateTime) >= secs) {
        database->start_work();
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
        database->commit();

        _lastRobotStatesUpdateTime = time;
    }
}

void CeleryWorker::OnUpdateEnd()
{
}

void CeleryWorker::_check_for_messages(const ::gazebo::common::UpdateInfo &info)
{
    //TOFO improve performance by choosing the correct memory order
    if (task_running.load(std::memory_order_seq_cst)) {
        // A task is already running, do not check for new tasks
        return;
    }
    std::cout << "Checking for celery task" << std::endl;
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

    const std::string task_name = message->HeaderTable().at("task").GetString();
    //TODO set task name from SDF
    if (task_name != "test_worker.test_robot") {
        channel->BasicReject(envelope, true);
        task_running.store(false, std::memory_order_seq_cst);
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
        channel->BasicReject(envelope, true);
        channel->BasicAck(envelope);
        std::cerr << "Inserting the previous robot immediately could cause problems in the simulation." << std::endl
                  << "Rejecting the task and sending it to the next worker" << std::endl;
        task_running.store(false, std::memory_order_seq_cst);
        return;
    }
    //_world->InsertModelString(SDFtext)
    _world->InsertModelSDF(robotSDF);

    double deadline = info.simTime.Double() + lifetime;
    _task_robot = std::make_tuple(name, nullptr, deadline);

    _database_robot_id = database->add_robot(name);
    database->add_evaluation(_database_robot_id, _evaluation_id, -1);

    // Don't leak memory
    // https://bitbucket.org/osrf/sdformat/issues/104/memory-leak-in-element
    //robotSDF.Root()->Reset();
}

void CeleryWorker::_reply(const std::string &reply_to, const std::string &task_id, Json::Value result) {
    const std::string &routing_key = reply_to;
    const std::string &correlation_id = task_id;
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
    //return_msg->HeaderTable({
    //                         {"id", "3149beef-be66-4b0e-ba47-2fc46e4edac3"},
    //                         {"task", "test_worker.add"}
    //                 });

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
    }
}
