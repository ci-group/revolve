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

#include <cstring>
#include <iostream>
#include <string>
#include <unistd.h>

#include "YamlBodyParser.h"

using namespace revolve::gazebo;

///////////////////////////////////////////////////
BodyPart::BodyPart()
{
  std::memset(neighbours_, 0, sizeof(neighbours_));
}

///////////////////////////////////////////////////
BodyPart::BodyPart(
        const std::string &name,
        const std::string &type,
        int x,
        int y,
        size_t rotation
)
        : name_(name)
        , type_(type)
        , x_(x)
        , y_(y)
        , rotation_(rotation)
{
  std::memset(neighbours_, 0, sizeof(neighbours_));
}

///////////////////////////////////////////////////
BodyPart::~BodyPart()
{
  // Delete dynamically allocated parents slots
  for (size_t parents_slot = 0; parents_slot < MAX_SLOTS; ++parents_slot)
  {
    delete neighbours_[parents_slot];
  }
}

///////////////////////////////////////////////////
YamlBodyParser::YamlBodyParser(const std::string &_genome)
{
  YAML::Node yaml_genome = YAML::Load(_genome);

  if (yaml_genome.IsNull())
  {
    std::cerr << "Failed to load a 'genome' code." << std::endl;
    std::exit(1);
  }

  this->Init(yaml_genome);
}

///////////////////////////////////////////////////
void YamlBodyParser::ParseFile(const std::string &_file_path)
{
  YAML::Node genome;
  if (access(_file_path.c_str(), F_OK) not_eq -1)
  {
    genome = YAML::LoadFile(_file_path);

    if (genome.IsNull())
    {
      std::cerr << "Failed to load a 'genome' file." << std::endl;
      std::exit(1);
    }
  }
  else
  {
    std::cerr << "Filename '" << _file_path << "' does not exist!" << std::endl;
    std::exit(1);
  }

  this->Init(genome);
}

///////////////////////////////////////////////////
void YamlBodyParser::ParseCode(const std::string &_code)
{
  YAML::Node genome = YAML::Load(_code);

  if (genome.IsNull())
  {
    std::cerr << "Failed to load a 'genome' code." << std::endl;
    std::exit(1);
  }

  this->Init(genome);
}

///////////////////////////////////////////////////
void YamlBodyParser::Init(const YAML::Node &_root)
{
  this->bodyMap_ = this->ParseModule(nullptr, _root["body"], 0, 0, 0);

  // Prepare matrices for defining coordinates and connections
  int range_x = this->maxX_ - this->minX_;
  int range_y = this->maxY_ - this->minY_;

  this->coordinates_.resize(this->numActuators_);
  this->connections_.resize(this->numActuators_);
  for (size_t i = 0; i < this->numActuators_; ++i)
  {
    this->coordinates_[i].resize(2);
    this->connections_[i].resize(numActuators_);
  }

  // Extract CPG coordinates matrix from a tree data structure
  this->SetNormalisedCoordinates(this->bodyMap_, range_x, range_y);

  // Extract connections matrix from a tree data structure
  this->SetConnections(this->bodyMap_);
}

///////////////////////////////////////////////////
YamlBodyParser::~YamlBodyParser()
{
  delete this->bodyMap_;
}

///////////////////////////////////////////////////
BodyPart *YamlBodyParser::ParseModule(
    BodyPart *_parent,
    const YAML::Node &_offspring,
    const size_t _rotation,
    int _x,
    int _y)
{
  BodyPart *module = nullptr;
  if (_offspring.IsDefined())
  {
    module = new BodyPart();
    module->name_ = _offspring["name"].IsDefined() ?
                   _offspring["name"].as< std::string >() :
                   _offspring["id"].as< std::string >();

    module->type_ = _offspring["type"].as< std::string >();
    module->rotation_ = _rotation;
    module->x_ = _x;
    module->y_ = _y;

    if (this->maxX_ < _x)
    { this->maxX_ = _x; }
    if (this->maxY_ < _y)
    { this->maxY_ = _y; }
    if (this->minX_ > _x)
    { this->minX_ = _x; }
    if (this->minY_ > _y)
    { this->minY_ = _y; }

    if (A_HINGE == module->type_)
    {
      this->numActuators_ += 1;
      module->id_ = this->numActuators_;
    }

    if (A_HINGE == module->type_ or P_HINGE == module->type_)
    {
      module->arity_ = 2;
    }
    else if (CORE == module->type_ or BRICK == module->type_)
    {
      module->arity_ = 4;
    }

    if (_offspring["children"].IsDefined())
    {
      module->neighbours_[0] = _parent;
      size_t parents_slot = (CORE == module->type_) ? 0 : 1;
      for (; parents_slot < MAX_SLOTS; ++parents_slot)
      {
        // Calculate coordinate for an offspring module
        int offsprings_x, offsprings_y;
        size_t offsprings_rotation =
            this->Rotation(module->arity_, parents_slot, module->rotation_);
        std::tie(offsprings_x, offsprings_y) =
            this->SetCoordinates(offsprings_rotation, _x, _y);

        // Traverse recursively through each of offspring modules
        module->neighbours_[parents_slot] = this->ParseModule(
            module,
            _offspring["children"][parents_slot],
            offsprings_rotation,
            offsprings_x,
            offsprings_y);
      }
    }
  }
  return module;
}

///////////////////////////////////////////////////
size_t YamlBodyParser::Rotation(
    const size_t _arity,
    const size_t _parent_slot,
    const size_t _parent_rotation) const
{
  if (_arity == 2)
  {
    return ((_parent_slot == 0) ? _parent_rotation + 2 : _parent_rotation) % 4;
  }
  else if (_arity == 4)
  {
    switch (_parent_slot)
    {
      case 0:
        return (_parent_rotation + 2) % 4;
      case 1:
        return _parent_rotation;
      case 2:
        return (_parent_rotation + 3) % 4;
      case 3:
        return (_parent_rotation + 1) % 4;
      default:
        std::cerr << "Unsupported parents slot provided." << std::endl;
        std::exit(-1);
    }
  }
  else
  {
    std::cerr << "Unsupported module arity provided." << std::endl;
    std::exit(-1);
  }
}

///////////////////////////////////////////////////
std::tuple< int, int > YamlBodyParser::SetCoordinates(
    const size_t _rotation,
    const int _init_x,
    const int _init_y)
{
  int x = _init_x;
  int y = _init_y;

  switch (_rotation)
  {
    case 0:
      x += 1;
      break;
    case 1:
      y += 1;
      break;
    case 2:
      x -= 1;
      break;
    case 3:
      y -= 1;
      break;
    default:
      std::cerr << "Wrong rotation calculated." << std::endl;
      std::exit(-1);
  }

  return std::make_tuple(x, y);
}

///////////////////////////////////////////////////
void YamlBodyParser::SetNormalisedCoordinates(
    BodyPart *_module,
    const int _range_x,
    const int _range_y)
{
  if (_module not_eq nullptr)
  {
    if (A_HINGE == _module->type_)
    {
      this->coordinates_[_module->id_ - 1][0] =
              (float)(_module->x_ * (2.0 / _range_x));
      this->coordinates_[_module->id_ - 1][1] =
              (float)(_module->y_ * (2.0 / _range_y));
    }

    size_t parents_slot = (CORE == _module->type_) ? 0 : 1;
    for (; parents_slot < MAX_SLOTS; ++parents_slot)
    {
      this->SetNormalisedCoordinates(
          _module->neighbours_[parents_slot],
          _range_x,
          _range_y);
    }
  }
}

///////////////////////////////////////////////////
void YamlBodyParser::SetConnections(BodyPart *_module)
{
  if (_module not_eq nullptr)
  {
    if (CORE == _module->type_ or BRICK == _module->type_)
    {
      for (size_t i = 0; i < MAX_SLOTS; ++i)
      {
        if (_module->neighbours_[i] not_eq nullptr
            and A_HINGE == _module->neighbours_[i]->type_)
        {
          for (size_t j = 0; j < MAX_SLOTS; ++j)
          {
            if (i not_eq j
                and _module->neighbours_[j] not_eq nullptr
                and A_HINGE == _module->neighbours_[j]->type_)
            {
              this->connections_
              [_module->neighbours_[i]->id_ - 1]
              [_module->neighbours_[j]->id_ - 1] = true;
            }
          }
        }
      }
    }

    size_t parents_slot = (CORE == _module->type_) ? 0 : 1;
    for (; parents_slot < MAX_SLOTS; ++parents_slot)
    {
      this->SetConnections(_module->neighbours_[parents_slot]);
    }
  }
}

///////////////////////////////////////////////////
ConnectionMatrix YamlBodyParser::Connections()
{
  return this->connections_;
}

///////////////////////////////////////////////////
CoordinatesMatrix YamlBodyParser::Coordinates()
{
  return this->coordinates_;
}
