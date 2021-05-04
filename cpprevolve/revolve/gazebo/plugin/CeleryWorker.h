//
// Created by matteo on 6/19/19.
//

#ifndef REVOLVE_CELERYWORKER_H
#define REVOLVE_CELERYWORKER_H

#include <gazebo/gazebo.hh>
#include <gazebo/physics/physics.hh>
#include <gazebo/common/common.hh>
#include <gazebo/msgs/msgs.hh>
#include <SimpleAmqpClient/SimpleAmqpClient.h>
#include <json/json.h>


namespace revolve {
namespace gazebo {

class CeleryWorker : public ::gazebo::WorldPlugin {
public:
    CeleryWorker();
    ~CeleryWorker() override;

    virtual void Load(
            ::gazebo::physics::WorldPtr _parent,
            sdf::ElementPtr _sdf) override;

    virtual void OnUpdateBegin(const ::gazebo::common::UpdateInfo &_info);
    virtual void OnUpdateEnd();

private:
    void _check_for_messages();
    void _reply(const std::string &reply_to, const std::string &task_id, Json::Value result);

private:
    AmqpClient::Channel::ptr_t channel;
    std::string consumer_tag;
    Json::StreamWriterBuilder builder;

    // Pointer to the update event connection
    ::gazebo::event::ConnectionPtr onBeginUpdateConnection;
    ::gazebo::event::ConnectionPtr onEndUpdateConnection;
};

}
}


#endif //REVOLVE_CELERYWORKER_H
