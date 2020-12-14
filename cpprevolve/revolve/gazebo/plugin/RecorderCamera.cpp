//
// Created by matteo on 12/7/20.
//

#include "RecorderCamera.h"
#include <gazebo/rendering/Camera.hh>
#include <sstream>

#define FPS 1

namespace rvgz = revolve::gazebo;

//////////////////////////////////////////////////
Ogre::PixelFormat OgrePixelFormat(const std::string &_format)
{
    Ogre::PixelFormat result;

    if (_format == "L8" || _format == "L_INT8")
        result = Ogre::PF_L8;
    else if (_format == "L16" || _format == "L_INT16" || _format == "L_UINT16")
        result = Ogre::PF_L16;
    else if (_format == "R8G8B8" || _format == "RGB_INT8")
        result = Ogre::PF_BYTE_RGB;
    else if (_format == "B8G8R8" || _format == "BGR_INT8")
        result = Ogre::PF_BYTE_BGR;
    else if (_format == "FLOAT32")
        result = Ogre::PF_FLOAT32_R;
    else if (_format == "FLOAT16")
        result = Ogre::PF_FLOAT16_R;
    else if (_format == "R16G16B16" || _format == "RGB_INT16"
             || _format == "RGB_UINT16")
        result = Ogre::PF_SHORT_RGB;
    else if ((_format == "BAYER_RGGB8") ||
             (_format == "BAYER_BGGR8") ||
             (_format == "BAYER_GBRG8") ||
             (_format == "BAYER_GRBG8"))
    {
        // let ogre generate rgb8 images for all bayer format requests
        // then post process to produce actual bayer images
        result = Ogre::PF_BYTE_RGB;
    }
    else
    {
        gzerr << "Error parsing image format (" << _format
              << "), using default Ogre::PF_R8G8B8\n";
        result = Ogre::PF_R8G8B8;
    }

    return result;
}

rvgz::RecorderCamera::RecorderCamera()
    : gz::CameraPlugin()
    , counter(0)
    , video(nullptr)
{}

void  rvgz::RecorderCamera::Load(gz::sensors::SensorPtr parent, sdf::ElementPtr sdf)
{
    CameraPlugin::Load(parent,sdf);

    // Camera follows target?
    // Programmatically, I think it should be possible to emit gui::Events::follow(<modelName>). And gui::Events::follow("") to stop following.
//    this->parentSensor->Camera()->SetTrackUseModelFrame(true);

    video = std::make_unique<::revolve::VideoFileStream>(
            "/tmp/diocane.mkv",
            parentSensor->UpdateRate(),
            cv::Size(parentSensor->ImageWidth(),parentSensor->ImageHeight())
    );
}

void rvgz::RecorderCamera::OnNewFrame(const unsigned char *image,
                                      unsigned int width,
                                      unsigned int height,
                                      unsigned int depth,
                                      const std::string &format)
{
    std::string camera_name = this->parentSensor->Camera()->Name();

    counter++;
    std::cout << "CameraCounter: " << counter << std::endl;

    if (!image)
    {
        std::cerr << "Can't save an empty image for camera: " << camera_name << std::endl;
        return;
    }

    std::stringstream ss_filename;
    ss_filename << "/tmp/recorder_camera_test_" << counter << '_' << ".png";

    Ogre::ImageCodec::ImageData *imgData;
    Ogre::Codec * pCodec;
    size_t size, pos;

    // Create image data structure
    imgData  = new Ogre::ImageCodec::ImageData();
    imgData->width  = width;
    imgData->height = height;
    imgData->depth  = depth;
    imgData->format = (Ogre::PixelFormat)OgrePixelFormat(format);
    size = gz::rendering::Camera::ImageByteSize(width, height, format);

    std::cout << "Image Data: " << std::endl
              << "\twidth : " << width  << std::endl
              << "\theight: " << height << std::endl
              << "\tdepth : " << depth  << std::endl
              << "\tformat: " << format << std::endl;

    ::revolve::FrameBufferRef frame(image, width, height, depth);

    (*video) << frame;
}

