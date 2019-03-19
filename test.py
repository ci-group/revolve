#!/usr/bin/env python3

import pyrevolve.revolve_bot

import sys
if __name__ == "__main__":
	with open('measures.csv','w') as file:
		file.write('id, branching, branching_modules_count, limbs, length_of_limbs, coverage, joints, hinge_count, active_hinges_count, brick_count, touch_sensor_count, brick_sensor_count, proportion, width, height, absolute_size, size, symmetry')
		file.write('\n')
		for r_id in range(0,100):
			try:
				print('Robot '+str(r_id))
				robot = pyrevolve.revolve_bot.RevolveBot()
				robot_path = "/home/vm/Downloads/offspringpop1/robot_{}.yaml".format(r_id)
				robot.load_file(robot_path)
				robot_ = robot.measure_body()
				file.write('{},'.format(r_id))
				for measure in robot_:
					file.write('{},'.format(robot_[measure]))
				file.write('\n')
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
