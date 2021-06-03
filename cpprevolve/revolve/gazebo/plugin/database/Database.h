/*
 * Copyright (C) 2015-2021 Vrije Universiteit Amsterdam
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
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
 * Author: Matteo De Carlo
 * Date: May 28, 2021
 *
 */
#ifndef REVOLVE_DATABASE_H
#define REVOLVE_DATABASE_H

#include <pqxx/pqxx>
#include <memory>
#include <ignition/math/Pose3.hh>
#include <gazebo/common/Time.hh>

namespace revolve::gazebo {

class Database {
private:
    std::unique_ptr<pqxx::connection> postgres = nullptr;
    std::unique_ptr<pqxx::work> pending_state_work = nullptr;
public:
    explicit Database(const std::string &dbname,
                      const std::string &username,
                      const std::string &password,
                      const std::string &address = "127.0.0.1",
                      unsigned int port = 5432);

    ~Database();

    void start_state_work();
    void commit_state_work();

    unsigned long add_robot(const std::string &robot_name);
    unsigned long get_robot(const std::string &robot_name);
    unsigned long update_robot(unsigned long robot_id, const std::string &robot_name);
    unsigned long add_or_get_robot(const std::string &robot_name);
    pqxx::result add_evaluation(unsigned long robot_id, unsigned long n, double fitness);
    pqxx::result update_evaluation(unsigned long robot_id, unsigned long n, double fitness);
    pqxx::result add_or_recreate_evaluation(unsigned long robot_id, unsigned long n, double fitness);
    pqxx::result drop_evaluation(unsigned long robot_id, unsigned long n);
    pqxx::result add_state(unsigned long robot_id, unsigned long eval_id, const ::gazebo::common::Time& time, const ignition::math::Pose3d &pose);
};
}

#endif //REVOLVE_DATABASE_H
