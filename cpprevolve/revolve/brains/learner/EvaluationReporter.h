//
// Created by matteo on 12/5/19.
//

#pragma once

#include <cassert>
#include <iostream>
#include <memory>
#include <vector>

namespace revolve {

// --------------------------------------------------------
/// Reporter Abstract Class
class EvaluationReporter
{
public:
    explicit EvaluationReporter(const std::string id)
        : robot_id(std::move(id))
    {}

    virtual ~EvaluationReporter() = default;

    virtual void report(
            unsigned int eval,
            bool dead,
            double fitness) = 0;

    const std::string robot_id;
};

// --------------------------------------------------------
/// Simple Reporter that prints the reported data on stdout
class PrintReporter : public EvaluationReporter
{
public:
    explicit PrintReporter(const std::string id)
        : EvaluationReporter(std::move(id))
    {}

    ~PrintReporter() override = default;

    void report(unsigned int eval,
                bool dead,
                double fitness) override
    {
        std::cout << "Evaluation Report: robot id("<< robot_id
                   << ") eval(" << eval
                   << ") dead(" << dead
                   << ") fitness(" << fitness
                   << ')' << std::endl;
    }
};

// --------------------------------------------------------
/// Aggregated Reporter
class AggregatedReporter : public EvaluationReporter
{
public:
    explicit AggregatedReporter(const std::string robot_id)
            : EvaluationReporter(std::move(robot_id))
    {}
    ~AggregatedReporter() override = default;

    void report(unsigned int eval,
                bool dead,
                double fitness) override
    {
        for (std::shared_ptr<EvaluationReporter> &reporter: reporters)
        {
            reporter->report(eval, dead, fitness);
        }
    }

    /// Create a new Reporter in place
    template<typename ReporterType, typename... Args>
    void create(Args &&... args)
    {
        reporters.emplace_back(new ReporterType(robot_id, std::forward<Args>(args)...));
    }

    void append(std::shared_ptr<EvaluationReporter> reporter)
    {
        assert(reporter->robot_id == this->robot_id);
        reporters.emplace_back(std::move(reporter));
    }

private:
    std::vector<std::shared_ptr<EvaluationReporter>> reporters;
};

}
