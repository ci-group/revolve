//
// Created by matteo on 12/7/20.
//

#ifndef REVOLVE_RECORDERCAMERA_H
#define REVOLVE_RECORDERCAMERA_H

#include <gazebo/gazebo.hh>
#include <gazebo/plugins/CameraPlugin.hh>
#include "VideoFileStream.h"
#include <memory>

namespace gz = ::gazebo;

namespace revolve {
namespace gazebo {

class RecorderCamera : public gz::CameraPlugin {
public:
    RecorderCamera();

    void Load(gz::sensors::SensorPtr parent, sdf::ElementPtr sdf) override;

    void OnNewFrame(const unsigned char *image,
                    unsigned int width,
                    unsigned int height,
                    unsigned int depth,
                    const std::string &format) override;
private:
    unsigned int counter;
    std::unique_ptr<::revolve::VideoFileStream> video;
};

}
}

#endif //REVOLVE_RECORDERCAMERA_H
