#!/usr/bin/env python3

import pyrevolve.revolve_bot

import sys
if __name__ == "__main__":

	for x in range(0, 10):
		try:
			print('robot '+str(x))
			robot = pyrevolve.revolve_bot.RevolveBot()
			robot_path = "/home/vm/Downloads/offspringpop1/robot_{}.yaml".format(x)
			robot.load_file(robot_path)
			x = robot.measure_body()
			print('size:{0}, width:{1}, height:{2}, abs_size:{3}'.format(x['size'], x['width'], x['height'], x['absolute_size']))
		except Exception as e:
			print('Exception {}'.format(e))

		# for x in range(0, 100):
		# 	try:
		# 		robot = pyrevolve.revolve_bot.RevolveBot()
		# 		robot_path = "/home/vm/Downloads/offspringpop1/robot_{}.yaml".format(x)
		# 		robot.load_file(robot_path)
		# 		robot.render2d('img/body_{}.png'.format(x))
		# 	except Exception as e:
		# 		print('Exception {}'.format(e))
