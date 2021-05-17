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
    void _robot_work(const ::gazebo::common::UpdateInfo &info);
    void _saveRobotState(const ::gazebo::common::UpdateInfo &info);
    void _check_for_messages(const ::gazebo::common::UpdateInfo &info);
    void _reply(const std::string &reply_to, const std::string &task_id, Json::Value result);

private:
    // RabbitMQ stuff
    volatile std::atomic<bool> task_running = ATOMIC_FLAG_INIT;
    /// optional tuple containing < Robot name, robot model pointer (may be null), deadline >
    boost::optional<std::tuple<std::string, ::gazebo::physics::ModelPtr, double>> _task_robot;
    AmqpClient::Channel::ptr_t channel;
    std::string consumer_tag;
    Json::CharReaderBuilder readerBuilder;
    Json::StreamWriterBuilder writerBuilder;
    std::string _reply_to;
    std::string _task_id;

    // Postgresql stuff
    /// Update frequency for the robot states to be uploaded into the simulator
    unsigned int _robotStatesUpdateFreq = 0;
    double _lastRobotStatesUpdateTime = 0;
    //TODO

    // Gazebo stuff
    ::gazebo::physics::WorldPtr _world;
    std::string last_robot_analyzed;

    ::gazebo::physics::PhysicsEnginePtr _physics;
    // Pointer to the update event connection, keep here to keep alive
    ::gazebo::event::ConnectionPtr onBeginUpdateConnection;
    ::gazebo::event::ConnectionPtr onEndUpdateConnection;
};

}
}


#endif //REVOLVE_CELERYWORKER_H
