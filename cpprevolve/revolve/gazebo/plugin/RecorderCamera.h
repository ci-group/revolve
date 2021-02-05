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
    virtual ~RecorderCamera() = default;

    void Load(gz::sensors::SensorPtr parent, sdf::ElementPtr sdf) override;

    void Init() override;

    void Reset() override;

    void OnNewFrame(const unsigned char *image,
                    unsigned int width,
                    unsigned int height,
                    unsigned int depth,
                    const std::string &format) override;

    std::string SaveFilePath() const;
    std::string SaveFileName() const;

private:
    void InitRecorder();
    ::gazebo::physics::ModelPtr SearchForRobotModel() const;
    void RobotModelFound();

private:
    unsigned int counter;
    unsigned int total_frames;

    /// \brief Video Recorder object
    std::unique_ptr<::revolve::VideoFileStream> video;

    /// \brief Pointer to the world
    ::gazebo::physics::WorldPtr world;
    /// \brief Pointer to the Recording Model
    ::gazebo::physics::ModelPtr camera_model;
    /// \brief Pointer to the robot
    ::gazebo::physics::ModelPtr robot;
    /// \brief Pointer to the plugin SDF structure
    sdf::ElementPtr SDF;

    // To print how many FPS the video recorder is doing,
    // without overwelming the program output
    float last_fps = -1;
};

}
}

#endif //REVOLVE_RECORDERCAMERA_H
