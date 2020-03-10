//
// Created by matteo on 17/06/19.
//

#ifndef REVOLVE_RASPBERRY_TIMER_H
#define REVOLVE_RASPBERRY_TIMER_H

#include <iostream>
#include <chrono>

class Timer
{
public:
    typedef std::chrono::high_resolution_clock Clock;
    typedef std::chrono::duration<double, std::ratio<1> > Seconds;

    Timer()
        : beg_(Clock::now())
        , last_step_(beg_)
    {}
    void reset() { beg_ = Clock::now(); }

    Seconds step() {
        std::chrono::time_point<Clock> prev = last_step_;
        last_step_ = Clock::now();
        return last_step_ - prev;
    }

    Seconds step_elapsed() const { return Clock::now() - last_step_; }
    Seconds elapsed() const { return last_step_ - beg_; }
    Seconds elapsed_now() const { return Clock::now() - beg_; }

    double step_double() { return into_double(step()); }
    double step_elapsed_double() const { return into_double(step_elapsed()); }
    double elapsed_double() const { return into_double(elapsed()); }
    double elapsed_now_double() const { return into_double(elapsed_now()); }

private:
    std::chrono::time_point<Clock> beg_;
    std::chrono::time_point<Clock> last_step_;

    template <typename T>
    static double into_double(const T &duration)
    {
        return std::chrono::duration_cast<Seconds>(duration).count();
    }
};

#endif //REVOLVE_RASPBERRY_TIMER_H
