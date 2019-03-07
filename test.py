#!/usr/bin/env python3

import pyrevolve.revolve_bot

import sys
if __name__ == "__main__":

	
		for x in range(0, 100):
			try:
				robot = pyrevolve.revolve_bot.RevolveBot()
				robot_path = "/home/vm/Downloads/offspringpop1/robot_{}.yaml".format(x)
				robot.load_file(robot_path)
				robot.render2d('img/body_{}.png'.format(x))
			except Exception as e: 
				print('Exception {}'.format(e))


