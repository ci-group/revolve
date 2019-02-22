#!/usr/bin/env python3

import pyrevolve.revolve_bot

if __name__ == "__main__":
    robot = pyrevolve.revolve_bot.RevolveBot()
    # robot.load_file("/home/karinemiras/projects/revolve/models/robot_26.yaml")
    robot.load_file("/home/karinemiras/projects/revolve/experiments/examples/yaml/robot_5.yaml")
    
    robot.save_file("/tmp/test.yaml")