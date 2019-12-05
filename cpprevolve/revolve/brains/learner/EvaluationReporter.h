//
// Created by matteo on 12/5/19.
//

#pragma once

#include <iostream>

namespace revolve {

// --------------------------------------------------------
/// Reporter Abstract Class
class EvaluationReporter
{
public:
    virtual ~EvaluationReporter() = default;

    virtual void report(
            unsigned int id,
            unsigned int eval,
            bool dead,
            float fitness) = 0;
};

// --------------------------------------------------------
/// Simple Reporter that prints the reported data on stdout
class PrintReporter : public EvaluationReporter
{
public:
    PrintReporter() = default;
    virtual ~PrintReporter() = default;

    void report(unsigned int id,
                unsigned int eval,
                bool dead,
                float fitness) override
    {
        std::cout << "Evaluation Report: robot id("<< id
                   << ") eval(" << eval
                   << ") dead(" << dead
                   << ") fitness(" << fitness
                   << ')' << std::endl;
    }
};

// --------------------------------------------------------
/// Aggregated Reporter
template<typename EvaluatorList>
class AggregatedReporter : public EvaluationReporter
{
public:
    explicit AggregatedReporter(EvaluatorList list)
            : list(std::move(list))
    {}
    virtual ~AggregatedReporter() = default;

    void report(unsigned int id,
                unsigned int eval,
                bool dead,
                float fitness) override
    {
        for (EvaluationReporter &reporter: list) {
            reporter.report(id, eval, dead, fitness);
        }
    }

private:
    EvaluatorList list;
};

}
