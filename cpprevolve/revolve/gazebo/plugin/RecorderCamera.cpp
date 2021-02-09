//
// Created by matteo on 12/7/20.
//

#include "RecorderCamera.h"
#include <gazebo/rendering/Camera.hh>
#include <gazebo/physics/PhysicsIface.hh>
#include <gazebo/physics/World.hh>
#include <gazebo/physics/Model.hh>
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
    this->camera_model = world->ModelByName("Recording");
    assert(camera_model);

    sdf::ElementPtr MovieLength = pluginSDF->GetElement("movie_length");
    double movie_length_seconds = std::stod(MovieLength->GetAttribute("seconds")->GetAsString());
    this->total_frames = static_cast<unsigned int>(movie_length_seconds * parentSensor->UpdateRate());
    std::cerr << "movie length seconds = " << movie_length_seconds << std::endl
              << "update rate          = " << parentSensor->UpdateRate() << std::endl
              << "total frames         = " << total_frames << std::endl;
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

    // Here we lock the physics so we are sure not to lose any frame for the video
    gz::physics::PhysicsEnginePtr physicsEngine = world->Physics();
    boost::recursive_mutex::scoped_lock lock_physics(*physicsEngine->GetPhysicsUpdateMutex());

    if (!robot) {
        robot = SearchForRobotModel();
        if (!robot) {
            // search again in the next frame, after the camera is moved on top of the robot
            return;
        }
        std::cerr << "MODEL FOUND! " << robot->GetName() << std::endl;
        // MODEL IS FINALLY FOUND
        this->RobotModelFound();
        // skip the first frame
        image = nullptr;
    }
    if (world->IsPaused()) {
        // don't capture frames if it's paused
        return;
    }

    assert(video);

    // reposition camera on top of the robot.
    // This code effectively makes the camera follow the robot
    ignition::math::Pose3d robot_pose = robot->WorldPose();
    ignition::math::Pose3d camera_pose = camera_model->WorldPose();
    camera_pose.Pos()[0] = robot_pose.Pos()[0] - 1.8;
    camera_pose.Pos()[1] = robot_pose.Pos()[1];
//    camera_pose.Pos()[2] = robot_pose.Pos()[2] + 2;

    camera_model->SetWorldPose(camera_pose);


    if (image == nullptr)
    {
        std::string camera_name = this->parentSensor->Camera()->Name();
        ::gazebo::common::Console::err(__FILE__, __LINE__) << "Can't save an empty image for camera: " << camera_name << std::endl;
        return;
    }

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

    //InitRecorder(); recorder is lazy-inited when the robot is found in the environemnt
    robot.reset();
    video.reset();
}

void revolve::gazebo::RecorderCamera::Reset()
{
    SensorPlugin::Reset();
    robot.reset();
    video.reset();
}

void revolve::gazebo::RecorderCamera::InitRecorder()
{
    std::string filename = this->SaveFileName();
    std::string filepath = this->SaveFilePath() + filename;

    // make sure path exists
    boost::filesystem::path folder_path = filepath;
    folder_path.remove_filename();
    boost::filesystem::create_directory(folder_path);

    ::gazebo::common::Console::msg() << "Saving video recording in \"" << filepath << "\"\n";

    video = std::make_unique<::revolve::VideoFileStream>(
            filepath.c_str(),
            parentSensor->UpdateRate(),
            cv::Size(parentSensor->ImageWidth(),parentSensor->ImageHeight())
    );
}

std::string revolve::gazebo::RecorderCamera::SaveFilePath() const
{
    return SDF->Get<std::string>("save_file_path");
}

std::string revolve::gazebo::RecorderCamera::SaveFileName() const
{
    return this->robot->GetName() + ".mp4";
}


::gazebo::physics::ModelPtr revolve::gazebo::RecorderCamera::SearchForRobotModel() const
{
    namespace gzp = ::gazebo::physics;
    gzp::Model_V models = world->Models();
    ::gazebo::common::Console::msg() << "Searching for robot:" << std::endl;

    gzp::ModelPtr robot_model;
    for (gzp::ModelPtr &model_ : models) {
        std::string model_name = model_->GetName();
        //std::string::rfind("string", 0) is a way of testing "starts_with"
        if (model_name.rfind("robot_", 0) == 0) {
            ::gazebo::common::Console::msg() << "ROBOT " << model_name << " FOUND!" << std::endl;
            robot_model = model_;
            break;
        }
    }
    return robot_model;
}

void revolve::gazebo::RecorderCamera::RobotModelFound()
{
    this->InitRecorder();
}
