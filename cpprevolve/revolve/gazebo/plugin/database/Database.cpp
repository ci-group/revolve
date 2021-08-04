//
// Created by matteo on 20/05/2021.
//

#include "Database.h"
#include <sstream>
#include <revolve/utils/Address.h>

using namespace revolve::gazebo;


Database::Database(const std::string &dbname,
                   const std::string &username,
                   const std::string &password,
                   const std::string &address,
                   unsigned int port)
{
    // Translate address in ip address
    ::revolve::utils::Address resolved_address(address, utils::Address::EITHER);

    for (const std::string &addr: resolved_address.get_ips_str()) {
        // Create connection string
        std::ostringstream connection_str;
        connection_str << "dbname = " << dbname
                       << " user = " << username
                       << " hostaddr = " << addr
                       << " port = " << port;
        std::cout << "Trying connection with " << connection_str.str() << std::endl;
        connection_str << " password = " << password;

        postgres = std::make_unique<pqxx::connection>(connection_str.str());
        if (postgres->is_open()) {
            break;
        }
    }

    if (!postgres->is_open()) {
        throw std::runtime_error("Could not open connection to postgresql!");
    } else {
        std::cout << "Connection to Database established" << std::endl;
    }
}

Database::~Database() {
    // postgres connection is automatically destroyed
    //postgres->close();
}

unsigned long Database::add_robot(const std::string &robot_name)
{
    std::ostringstream sql;
    sql << "INSERT INTO robot (id, name) "  \
           "VALUES ( DEFAULT, " << postgres->quote(robot_name) << " ) "
           "RETURNING id;";
    pqxx::work work(*postgres);
    auto result = work.exec(sql.str());
    work.commit();
    unsigned long robot_id = result.at(0)[0].as<unsigned long>();
    return robot_id;
}

unsigned long Database::get_robot(const std::string &robot_name)
{
    std::ostringstream sql;
    sql << "SELECT id "  \
           " FROM robot"
           " WHERE name=" << postgres->quote(robot_name) << ';';
    pqxx::read_transaction work(*postgres);
    auto result = work.exec(sql.str());
    work.commit();
    unsigned long robot_id = result.at(0)[0].as<unsigned long>();
    return robot_id;
}

unsigned long Database::update_robot(unsigned long robot_id, const std::string &robot_name)
{
    std::ostringstream sql;
    sql << "UPDATE robot "  \
           " SET name=" << postgres->quote(robot_name) <<
           " WHERE id=" << robot_id <<
           " RETURNING id;";
    pqxx::work work(*postgres);
    auto result = work.exec(sql.str());
    work.commit();
    unsigned long inserted_robot_id = result.at(0)[0].as<unsigned long>();
    assert(inserted_robot_id == robot_id);
    return robot_id;
}

unsigned long Database::add_or_get_robot(const std::string &robot_name)
{
    try {
        return add_robot(robot_name);
    } catch (const pqxx::unique_violation &e) {
        std::string message = e.what();
        if (message.find("duplicate key value violates unique constraint \"robot_name_key\"") != std::string::npos) {
            // found! we get in this case
            return get_robot(robot_name);
        }
        std::clog << "####### pqxx::unique_violation #######" << std::endl;
        std::clog << "what()    : " << e.what() << std::endl;
        std::clog << "query()   : " << e.query() << std::endl;
        std::clog << "sqlstate(): " << e.sqlstate() << std::endl;
        throw; // re-throwing the same error
    }
}

pqxx::result Database::add_evaluation(unsigned long robot_id, unsigned long n, double fitness) {
    std::ostringstream sql;
    sql << "INSERT INTO robot_evaluation (robot_id, n, fitness) "
           "VALUES ( " << robot_id << ", " << n << ", " << fitness << ");";
    pqxx::work work(*postgres);
    auto result = work.exec(sql.str());
    work.commit();
    return result;
}

pqxx::result Database::update_evaluation(unsigned long robot_id, unsigned long n, double fitness) {
    std::ostringstream sql;
    sql << "UPDATE robot_evaluation"
           "SET robot_id="", n="", fitness="") "
           "WHERE ";
    pqxx::work work(*postgres);
    auto result = work.exec(sql.str());
    work.commit();
    return result;
}

pqxx::result Database::add_or_recreate_evaluation(unsigned long robot_id, unsigned long n, double fitness)
{
    try {
        return add_evaluation(robot_id, n, fitness);
    } catch (const pqxx::unique_violation &e) {
//        std::clog << "####### pqxx::unique_violation #######" << std::endl;
//        std::clog << "what()    : " << e.what() << std::endl;
//        std::clog << "query()   : " << e.query() << std::endl;
//        std::clog << "sqlstate(): " << e.sqlstate() << std::endl;
        drop_evaluation(robot_id, n);
        return add_evaluation(robot_id, n, fitness);
    }
}

pqxx::result Database::drop_evaluation(unsigned long robot_id, unsigned long n)
{
    std::ostringstream sql_state;
    sql_state << "DELETE FROM robot_state"
                 " WHERE evaluation_robot_id=" << robot_id <<
                 " AND evaluation_n=" << n << ';';
    pqxx::work work(*postgres);
    auto result = work.exec(sql_state.str());

    std::ostringstream sql_eval;
    sql_eval << "DELETE FROM robot_evaluation"
                " WHERE robot_id=" << robot_id <<
                " AND n=" << n << ';';
    auto result2 = work.exec(sql_eval.str());

    work.commit();
    return result2;
}

pqxx::result Database::add_state(unsigned long robot_id,
                                 unsigned long eval_id,
                                 const ::gazebo::common::Time& time,
                                 const ignition::math::Pose3d &pose)
{
    std::ostringstream sql;
    const ignition::math::Vector3d &position = pose.Pos();
    const ignition::math::Quaterniond &rot = pose.Rot();
    sql << "INSERT INTO robot_state ( "
           "time_sec,time_nsec,evaluation_n,evaluation_robot_id,"
           "pos_x,pos_y,pos_z,"
           "rot_quaternion_x,rot_quaternion_y,rot_quaternion_z,rot_quaternion_w,"
           "orientation_forward,orientation_left,orientation_back,orientation_right"
           " ) "
           "VALUES ("
           << time.sec << ',' << time.nsec << ',' << eval_id << ',' << robot_id << ','
           << position.X() << ',' << position.Y() << ',' << position.Z() << ','
           << rot.X() << ',' << rot.Y() << ',' << rot.Z() << ',' << rot.W() << ','
           << "0,0,0,0"
           << " ); ";
    auto result = pending_state_work->exec(sql.str());
    // do not commit every single state, buffer them instead in the `pending_work` :)
    return result;
}

void Database::start_state_work() {
    assert(!pending_state_work);
    pending_state_work = std::make_unique<pqxx::work>(*postgres);
}

void Database::commit_state_work() {
    assert(pending_state_work);
    pending_state_work->commit();
    pending_state_work.reset();
}
