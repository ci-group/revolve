//
// Created by matteo on 6/19/19.
//

#include <gazebo/common/Events.hh>
#include <gazebo/gazebo.hh>
#include <gazebo/physics/physics.hh>
#include <gazebo/common/common.hh>
#include <gazebo/msgs/msgs.hh>
#include "CeleryWorker.h"

using namespace revolve::gazebo;

CeleryWorker::CeleryWorker()
{
    builder.settings_["indentation"] = "";
}

CeleryWorker::~CeleryWorker()
{

}

void CeleryWorker::Load(::gazebo::physics::WorldPtr _parent, sdf::ElementPtr _sdf)
{

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
}

void CeleryWorker::OnUpdateBegin(const ::gazebo::common::UpdateInfo &_info)
{
    // here we know what time is it in the simulator
}

void CeleryWorker::OnUpdateEnd()
{
    this->_check_for_messages();
}

void CeleryWorker::_check_for_messages() {

    std::cout << "Checking for celery task" << std::endl;
    AmqpClient::Envelope::ptr_t envelope;
    auto message_received = channel->BasicConsumeMessage(
            consumer_tag,
            envelope,
            1000);
    if (!message_received)
        return; // no message

    auto message = envelope->Message();
    auto reply_to = message->ReplyTo();

    const std::string &body_string = message->Body();
    std::cout << "Received task: " << body_string << std::endl;
    Json::Value body;
    JSONCPP_STRING err;
    Json::CharReaderBuilder builder;
    const std::unique_ptr<Json::CharReader> reader(builder.newCharReader());
    const char *start = body_string.c_str();
    const char *end = start + body_string.length() -1;
    bool error = reader->parse(start, end, &body, &err);
    if (error) {
        std::cerr << "error parsing json" << err << std::endl;
        channel->BasicReject(envelope, false);
        channel->BasicCancel(consumer_tag);
        return; //error
    }

    // Parse JSON REQUEST
    const std::string &task_id = message->HeaderTable().at("id").GetString();

    std::cout << "working on task: " << task_id << std::endl;

    //TODO extract the robot SDF and the robot lifetime from the request
    const int x = body[0][0].asInt();
    const int y = body[0][1].asInt();

    const int result = x + y;

    // Work done
    std::cout << "Working done " << std::endl;
    channel->BasicAck(envelope);

    // Reply with the result to celery:
    this->_reply(reply_to, task_id, result);
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

    const std::string serialized = Json::writeString(builder, msg);
    const std::string serialized2 = Json::writeString(builder, msg);

    auto return_msg = AmqpClient::BasicMessage::Create(serialized);
    return_msg->ContentType("application/json");
    return_msg->ContentEncoding("utf-8");
    //return_msg->HeaderTable({
    //                         {"id", "3149beef-be66-4b0e-ba47-2fc46e4edac3"},
    //                         {"task", "test_worker.add"}
    //                 });

    channel->BasicPublish("", routing_key, return_msg);
}