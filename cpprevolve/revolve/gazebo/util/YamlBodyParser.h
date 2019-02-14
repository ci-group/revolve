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
* Description: Utility file for parsing robot's YAML tree-structure.
* Author: Milan Jelisavcic
* Date: November 23, 2017
*
*/

#ifndef PARSEYAMLGENOME_YAMLBODYPARSER_H
#define PARSEYAMLGENOME_YAMLBODYPARSER_H

#include <string>
#include <memory>
#include <tuple>
#include <vector>

#include <yaml-cpp/yaml.h>

namespace revolve
{
  namespace gazebo
  {
    const std::string CORE = "Core";

    const std::string A_HINGE = "ActiveHinge";

    const std::string P_HINGE = "PassiveHinge";

    const std::string BRICK = "FixedBrick";

    const size_t MAX_SLOTS = 4;

    class BodyPart
    {
      /// \brief Constructor
      public: BodyPart();

      /// \brief Constructor
      public: BodyPart(
          const std::string &name,
          const std::string &type,
          int x,
          int y,
          size_t rotation);

      /// \brief Destructor
      public: ~BodyPart();

      /// \brief Name of a module
      public: std::string name_ = "none";

      /// \brief Type of a module
      public: std::string type_ = "none";

      /// \brief X coordinate of a module
      public: int x_ = 0;

      /// \brief Y coordinate of a module
      public: int y_ = 0;

      /// \brief ID of a module
      public: size_t id_ = 0;

      /// \brief Arity of a module
      public: size_t arity_ = 4;

      /// \brief Rotation of a module
      public: size_t rotation_ = 0;

      /// \brief Neighbouring slots of a module
      public: BodyPart *neighbours_[MAX_SLOTS];
    };

    typedef std::vector< std::vector< bool>> ConnectionMatrix;

    typedef std::vector< std::vector< float>> CoordinatesMatrix;

    class YamlBodyParser
    {
      /// \brief Constructor
      /// \param[in] _genome YAML-formatted string of a robot's genome
      public: YamlBodyParser(const std::string &_genome);

      /// \brief Destructor
      public: ~YamlBodyParser();

      /// \brief Return connections of a body
      public: ConnectionMatrix Connections();

      /// \brief Return coordinates of a body
      public: CoordinatesMatrix Coordinates();

      /// \brief Parse file based on the file path
      public: void ParseFile(const std::string &_file_path);

      /// \brief Parse code
      public: void ParseCode(const std::string &_code);

      /// \brief Parse body structure based on loaded YAML code
      private: void Init(const YAML::Node &_root);

      /// \brief Recursivelly parse nodes in a YAML-tree structure
      private: BodyPart *ParseModule(
          BodyPart *_parent,
          const YAML::Node &_offspring,
          const size_t _rotation,
          int _x,
          int _y);

      /// \brief Calculate a relative rotaion based on parent's features
      private: size_t Rotation(
          const size_t _arity,
          const size_t _parent_slot,
          const size_t _parent_rotation) const;

      /// \brief Calculate coordinates of a module
      private: std::tuple< int, int > SetCoordinates(
          const size_t _rotation,
          const int _init_x,
          const int _init_y);

      /// \brief Define normalised coordinates of a module
      private: void SetNormalisedCoordinates(
          BodyPart *_module,
          const int _range_x,
          const int _range_y);

      /// \brief Define connections of neighbouring actuators
      private: void SetConnections(BodyPart *_module);

      /// \brief Number of actuators
      private: size_t numActuators_ = 0;

      /// \brief Maximal X coordinate of robot's modules
      private: int maxX_ = 0;

      /// \brief Maximal Y coordinate of robot's modules
      private: int maxY_ = 0;

      /// \brief Minimal X coordinate of robot's modules
      private: int minX_ = 0;

      /// \brief Minimal Y coordinate of robot's modules
      private: int minY_ = 0;

      /// \brief Start of body map defined during run-time
      private: BodyPart *bodyMap_ = nullptr;

      /// \brief Deterimned connections of a robot's modules
      private: ConnectionMatrix connections_;

      /// \brief Deterimned coordinates of a robot's modules
      private: CoordinatesMatrix coordinates_;
    };
  }
}

#endif  // PARSEYAMLGENOME_YAMLBODYPARSER_H
