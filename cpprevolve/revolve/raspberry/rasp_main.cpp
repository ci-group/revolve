//
// Created by matteo on 14/06/19.
//

#include "RaspController.h"
#include "Servo.h"

void reset(short pin);

int main( int argc, const char* argv[] )
{
//    revolve::RaspController controller();
    reset(1);
}

void reset(short pin)
{
    revolve::Servo s(0,0,0,pin);
    s.center();
}