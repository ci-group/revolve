/*
* Copyright (C) 2017 Vrije Universiteit Amsterdam
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
* Description: TODO: <Add brief description about file purpose>
* Author: Elte Hupkes
*
*/

//
// Created by elte on 6-6-15.
//

#ifndef REVOLVE_CELERYWORLDCONTROLLER_H
#define REVOLVE_CELERYWORLDCONTROLLER_H

#include <map>
#include <string>
#include <queue>
#include <SimpleAmqpClient/SimpleAmqpClient.h>
#include <json/json.h>

#include <boost/thread/mutex.hpp>

#include <gazebo/gazebo.hh>
#include <gazebo/physics/physics.hh>
#include <gazebo/common/common.hh>
#include <gazebo/msgs/msgs.hh>

#include <revolve/msgs/model_inserted.pb.h>
#include <revolve/msgs/robot_states.pb.h>

namespace revolve {
namespace gazebo {

class CeleryWorldController: public ::gazebo::WorldPlugin
{
public:
    CeleryWorldController();

    virtual ~CeleryWorldController();

    virtual void Load(
            ::gazebo::physics::WorldPtr _parent,
            sdf::ElementPtr _sdf) override;

    virtual void Reset() override;

protected:
    // Listener for analysis requests
    virtual void HandleRequest(ConstRequestPtr &request);

    // Listener for entity delete responses
    virtual void HandleResponse(ConstResponsePtr &request);

    // Callback for model insertion
    virtual void OnModel(ConstModelPtr &msg);

    // Method called
    virtual void OnBeginUpdate(const ::gazebo::common::UpdateInfo &_info);

    virtual void OnEndUpdate();

    virtual void OnContacts(ConstContactsPtr &msgContacts);

    // Maps model names to insert request IDs
    // model_name -> request_id, SDF, insert_operation_pending
    std::map<std::string, std::tuple<int, std::string, bool> > insertMap_;

    // Queue of `delete_robot` requests
    std::queue<std::tuple<::gazebo::physics::ModelPtr, int>> delete_robot_queue;

    // Stores the world
    ::gazebo::physics::WorldPtr world_;

    // Transport node
    ::gazebo::transport::NodePtr node_;

    // Mutex for the insertMap_
    boost::mutex insertMutex_;

    // Mutex for message writing
    boost::mutex dataMutex_;

    // Mutex for the deleteMap_
    boost::mutex deleteMutex_;

    // request subscriber
    ::gazebo::transport::SubscriberPtr contactsSub_;

    // Request subscriber
    ::gazebo::transport::SubscriberPtr requestSub_;

    // Request publisher
    ::gazebo::transport::PublisherPtr requestPub_;

    // Response subscriber
    ::gazebo::transport::SubscriberPtr responseSub_;

    // Response publisher
    ::gazebo::transport::PublisherPtr responsePub_;

    // Subscriber for actual model insertion
    ::gazebo::transport::SubscriberPtr modelSub_;

    // Publisher for periodic robot poses
    ::gazebo::transport::PublisherPtr robotStatesPub_;

    // Frequency at which robot info is published
    // Defaults to 0, which means no update at all
    unsigned int robotStatesPubFreq_;

    // Pointer to the update event connection
    ::gazebo::event::ConnectionPtr onBeginUpdateConnection;
    ::gazebo::event::ConnectionPtr onEndUpdateConnection;

    // Last (simulation) time robot info was sent
    double lastRobotStatesUpdateTime_;

    // Death sentence list. It collects all the end time for all robots that have
    // a death sentence
    // NEGATIVE DEATH SENTENCES mean total lifetime, death sentence not yet initialized.
    std::map<std::string, double> death_sentences_;

    // Mutex for the deleteMap_
    boost::mutex death_sentences_mutex_;

//    boost::mutex world_insert_remove_mutex;

    ::gazebo::physics::Model_V models_to_remove;

    // celery consumer functionality
    AmqpClient::Channel::ptr_t celeryChannel;
    std::string consumer_tag;
    AmqpClient::Envelope::ptr_t envelope;

    bool running;

    Json::FastWriter fastWriter;
    Json::Value rootmsg;
    Json::Value root;   // will contains the root value after parsing.
    Json::Reader reader;
};

}  // namespace gazebo
}  // namespace revolve

#endif  // REVOLVE_CELERYCeleryWorldController_H
