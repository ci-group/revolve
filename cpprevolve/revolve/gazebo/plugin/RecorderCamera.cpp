//
// Created by matteo on 12/7/20.
//

#include "RecorderCamera.h"
#include <gazebo/rendering/Camera.hh>
#include <gazebo/physics/PhysicsIface.hh>
#include <gazebo/physics/World.hh>
#include <gazebo/physics/PhysicsEngine.hh>
#include <gazebo/sensors/CameraSensor.hh>
#include <sstream>
#include <string>

namespace rvgz = revolve::gazebo;

rvgz::RecorderCamera::RecorderCamera()
    : gz::CameraPlugin()
    , counter(0)
    , total_frames(0)
    , video(nullptr)
{}

void  rvgz::RecorderCamera::Load(gz::sensors::SensorPtr parent, sdf::ElementPtr pluginSDF)
{
    CameraPlugin::Load(parent, pluginSDF);

    std::string world_name = parent->WorldName();
    this->world = gz::physics::get_world(world_name);

    this->SDF = pluginSDF;

    sdf::ElementPtr MovieLength = pluginSDF->GetElement("movie_length");
    double movie_length_seconds = std::stod(MovieLength->GetAttribute("seconds")->GetAsString());
    this->total_frames = static_cast<unsigned int>(movie_length_seconds * parentSensor->UpdateRate());
    std::cerr << "movie length seconds = " << movie_length_seconds << std::endl
              << "update rate          = " << parentSensor->UpdateRate() << std::endl
              << "total frames         = " << total_frames << std::endl;
//    this->world = parent->GetWorld();
}

void rvgz::RecorderCamera::OnNewFrame(const unsigned char *image,
                                      unsigned int width,
                                      unsigned int height,
                                      unsigned int depth,
                                      const std::string &/*format*/)
{
    // Format is actually broken. Says RGB format, image is BGR.

    // Check if video is finished
    if (counter > total_frames) {
        //TODO remove print
        std::cerr << "FINI: counter > total_frames: " << counter << " > " << total_frames << std::endl;
        return;
    }
    if (world->IsPaused()) {
        // don't capture frames if it's paused
        return;
    }

    if (image == nullptr)
    {
        std::string camera_name = this->parentSensor->Camera()->Name();
        ::gazebo::common::Console::err(__FILE__, __LINE__) << "Can't save an empty image for camera: " << camera_name << std::endl;
        return;
    }

    // Here we lock the physics so we are sure not to lose any frame for the video
    gz::physics::PhysicsEnginePtr physicsEngine = world->Physics();
    boost::recursive_mutex::scoped_lock lock_physics(*physicsEngine->GetPhysicsUpdateMutex());

    counter++;

    // format reported to be R8G8B8 while actually is B8G8R8
    ::revolve::FrameBuffer frame(image, width, height, depth);

    float fps = camera->AvgFPS();
    if (fps != last_fps) {
        std::cout << "FPS " << fps << std::endl;
        last_fps = fps;
    }

    (*video) << frame;

    // Check if video is finished
    if (counter > total_frames) {
        // delete the video object closes the video stream
        ::gazebo::common::Console::msg() << "Video finished, closing the plugin" << std::endl;
        video.reset(nullptr);
        this->camera->Fini();
        lock_physics.release();
        ::gazebo::common::Console::msg() << "EXIT" << std::endl;
        std::exit(0);
        //this->parentSensor->Fini();
    }
}

void revolve::gazebo::RecorderCamera::Init()
{
    ::gazebo::common::Console::msg() << "rvgz::RecorderCamera::Init\n";
    SensorPlugin::Init();
    //this->parentSensor->ConnectUpdated()

    // Camera follows target?
    // Programmatically, I think it should be possible to emit gui::Events::follow(<modelName>). And gui::Events::follow("") to stop following.
    //this->parentSensor->Camera()->SetTrackUseModelFrame(true);
    InitRecorder();
}

void revolve::gazebo::RecorderCamera::Reset()
{
    SensorPlugin::Reset();
    this->InitRecorder();
}

void revolve::gazebo::RecorderCamera::InitRecorder()
{
    std::string filename = this->SaveFilePath();

    // make sure path exists
    boost::filesystem::path folder_path = filename;
    folder_path.remove_filename();
    boost::filesystem::create_directory(folder_path);

    ::gazebo::common::Console::msg() << "Saving video recording in \"" << filename << "\"\n";

    video = std::make_unique<::revolve::VideoFileStream>(
            filename.c_str(),
            parentSensor->UpdateRate(),
            cv::Size(parentSensor->ImageWidth(),parentSensor->ImageHeight())
    );
}

std::string revolve::gazebo::RecorderCamera::SaveFilePath() const
{
    return SDF->Get<std::string>("save_file_path");
}

