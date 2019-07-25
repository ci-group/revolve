//
// Created by matteo on 6/19/19.
//

#ifndef REVOLVE_TORUSWORLD_H
#define REVOLVE_TORUSWORLD_H

#include <gazebo/gazebo.hh>
#include <gazebo/physics/physics.hh>
#include <gazebo/common/common.hh>
#include <gazebo/msgs/msgs.hh>


namespace revolve {
namespace gazebo {

class TorusWorld : public ::gazebo::WorldPlugin {
public:
    TorusWorld();
    ~TorusWorld() override;

    virtual void Load(
            ::gazebo::physics::WorldPtr _parent,
            sdf::ElementPtr _sdf) override;

    virtual void OnUpdate(const ::gazebo::common::UpdateInfo &_info);

private:

    // Pointer to the update event connection
    ::gazebo::event::ConnectionPtr onBeginUpdateConnection;
    ::gazebo::event::ConnectionPtr onEndUpdateConnection;
};

}
}


#endif //REVOLVE_TORUSWORLD_H
