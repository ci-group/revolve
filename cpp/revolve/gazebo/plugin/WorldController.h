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

#ifndef REVOLVE_WORLDCONTROLLER_H
#define REVOLVE_WORLDCONTROLLER_H

#include <map>
#include <string>

#include <boost/thread/mutex.hpp>

#include <gazebo/gazebo.hh>
#include <gazebo/physics/physics.hh>
#include <gazebo/common/common.hh>
#include <gazebo/msgs/msgs.hh>

#include <revolve/msgs/model_inserted.pb.h>
#include <revolve/msgs/robot_states.pb.h>

namespace revolve
{
  namespace gazebo
  {
    class WorldController
            : public ::gazebo::WorldPlugin
    {
      public:
      WorldController();

      virtual void Load(
              ::gazebo::physics::WorldPtr _parent,
              sdf::ElementPtr _sdf);

      protected:
      // Listener for analysis requests
      virtual void HandleRequest(ConstRequestPtr &request);

      // Listener for entity delete responses
      virtual void HandleResponse(ConstResponsePtr &request);

      // Callback for model insertion
      virtual void OnModel(ConstModelPtr &msg);

      // Method called
      virtual void OnUpdate(const ::gazebo::common::UpdateInfo &_info);

      // Maps model names to insert request IDs
      std::map< std::string, int > insertMap_;

      // Maps `entity_delete` IDs to `delete_robot` ids
      std::map< int, int > deleteMap_;

      // Stores the world
      ::gazebo::physics::WorldPtr world_;

      // Transport node
      ::gazebo::transport::NodePtr node_;

      // Mutex for the insertMap_
      boost::mutex insertMutex_;

      // Mutex for the deleteMap_
      boost::mutex deleteMutex_;

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
      ::gazebo::event::ConnectionPtr updateConnection_;

      // Last (simulation) time robot info was sent
      double lastRobotStatesUpdateTime_;
    };
  } // namespace gazebo
} // namespace revolve

#endif  // REVOLVE_WORLDCONTROLLER_H
