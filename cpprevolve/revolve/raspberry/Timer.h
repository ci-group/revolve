//
// Created by matteo on 17/06/19.
//

#ifndef REVOLVE_TIMER_H
#define REVOLVE_TIMER_H
#include <iostream>
#include <chrono>

class Timer
{
public:
    Timer()
        : beg_(clock_::now())
        , last_step_(beg_)
    {}
    void reset() { beg_ = clock_::now(); }
    double step() {
        std::chrono::time_point<clock_> prev = last_step_;
        last_step_ = clock_::now();
        return time_difference(prev, last_step_);
    }
    double elapsed() const { return time_difference(beg_, last_step_); }

private:
    typedef std::chrono::high_resolution_clock clock_;
    typedef std::chrono::duration<double, std::ratio<1> > second_;
    std::chrono::time_point<clock_> beg_;
    std::chrono::time_point<clock_> last_step_;

    static double time_difference(const std::chrono::time_point<clock_> start, const std::chrono::time_point<clock_> end)
    {
        return std::chrono::duration_cast<second_>
                (end - start).count();
    }
};

#endif //REVOLVE_TIMER_H
