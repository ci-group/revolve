//
// Created by matteo on 20/05/2021.
//

#ifndef REVOLVE_DATABASE_H
#define REVOLVE_DATABASE_H

#include <pqxx/pqxx>
#include <memory>
#include <ignition/math/Pose3.hh>
#include <gazebo/common/Time.hh>

namespace revolve {
namespace gazebo {

class Database {
private:
    std::unique_ptr<pqxx::connection> postgres = nullptr;
    std::unique_ptr<pqxx::work> pending_work = nullptr;
public:
    explicit Database(const char *dbname,
                      const char *username = "username",
                      const char *password = "password",
                      const char *address = "::1",
                      unsigned int port = 5432);

    ~Database();

    void start_work();
    void commit();

    unsigned long add_robot(const std::string &robot_name);
    pqxx::result add_evaluation(unsigned int robot_id, unsigned int n, double fitness);
    pqxx::result add_state(unsigned int robot_id, unsigned int eval_id, const ::gazebo::common::Time& time, const ignition::math::Pose3d &pose);
};
}
}

#endif //REVOLVE_DATABASE_H
