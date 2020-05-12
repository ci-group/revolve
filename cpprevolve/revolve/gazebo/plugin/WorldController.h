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
* Author: Elte Hupkes and Matteo De Carlo
*
*/

#pragma once

#include <map>
#include <string>
#include <queue>

#include <boost/thread/mutex.hpp>

#include <gazebo/gazebo.hh>
#include <gazebo/physics/physics.hh>
#include <gazebo/common/common.hh>
#include <gazebo/msgs/msgs.hh>

#include <revolve/msgs/model_inserted.pb.h>
#include <revolve/msgs/robot_states.pb.h>
#include <revolve/msgs/robot_states_learning.pb.h>

namespace revolve {
namespace gazebo {

class WorldController : public ::gazebo::WorldPlugin
{
public:
    WorldController();

    ~WorldController() override;

    void Load(
            ::gazebo::physics::WorldPtr _parent,
            sdf::ElementPtr _sdf) override;

    void Reset() override;

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

    void OnRobotReport(const boost::shared_ptr<revolve::msgs::LearningRobotStates const> &msg);

protected:
    const bool enable_parallelization;

    // Maps model names to insert request IDs
    // model_name -> request_id, SDF, insert_operation_pending
    std::map<std::string, int> insertMap_;

    // Stores the world
    ::gazebo::physics::WorldPtr world_;

    // Transport node
    ::gazebo::transport::NodePtr node_;

    // Mutex for the insertMap_
    boost::mutex insertMutex_;

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

    // Subscriber for periodic robot learning reports
    ::gazebo::transport::SubscriberPtr robotLearningStatesSub;

    // Pointer to the update event connection
    ::gazebo::event::ConnectionPtr onBeginUpdateConnection;
    ::gazebo::event::ConnectionPtr onEndUpdateConnection;

    boost::mutex model_remove_mutex;
    ::gazebo::physics::Model_V models_to_remove;
};

}  // namespace gazebo
}  // namespace revolve
