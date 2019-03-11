import cairo
from .canvas import Canvas
from .grid import Grid

class Render:

	def __init__(self):
		"""Instantiate grid"""
		self.grid = Grid()


	def get_keys(self, body):
		"""Returns the postition of the slots of the children"""
		return list(body.keys())

	def get_children(self, body):
		"""Return children of body, False if no children present"""
		if 'children' in body:
			return body['children']
		else:
			return False

	def get_type(self, body):
		"""Return the type of the module"""
		return body['type']

	def get_id(self, body):
		"""Return the id of the module"""
		return body['id']

	def get_orientation(self, body):
		"""Return the orientation of the module (hinge)"""
		return body['orientation']

	def parse_body_to_draw(self, body, canvas):
		"""Parse the body to the canvas to draw the png"""
		children_keys = self.get_keys(body)
		for key in children_keys:
			# Move in direction of specified slot
			canvas.move_by_slot(key)
			mod_type = self.get_type(body[key])
			r_orientation = self.get_orientation(body[key])
			if mod_type == 'ActiveHinge':
				Canvas.rotating_orientation += r_orientation
				canvas.draw_hinge()
				canvas.draw_connector_to_parent()
			elif mod_type == 'FixedBrick':
				Canvas.rotating_orientation += r_orientation
				canvas.draw_module()
				canvas.draw_connector_to_parent()
			elif mod_type == 'TouchSensor':
				Canvas.rotating_orientation += r_orientation
				canvas.save_sensor_position()
			else:
				# Unknown element, move back to previous state and jump out of loop
				self.grid.move_back()
				continue

			children = self.get_children(body[key])
			if not children:
				# Element has no children, move back to previous state and jump out of the loop
				canvas.move_back()
				continue
			
			keys = self.get_keys(children)
			if keys:
				# Traverse children of element to draw on canvas
				self.parse_body_to_draw(children, canvas)
		# Parent has no more children, move back to previous state
		canvas.move_back()
				
	def traverse_path_of_robot(self, body):
		"""Traverse path of robot to obtain visited coordinates"""
		children_keys = self.get_keys(body)
		for key in children_keys:
			# Move in direction of specified slot
			self.grid.move_by_slot(key)
			type = self.get_type(body[key])
			if type == 'ActiveHinge' or type == 'FixedBrick' or type == 'TouchSensor':
				self.grid.add_to_visited()
			else:
				# Unknown element, move back to previous state and jump out of the loop
				self.grid.move_back()
				continue

			children = self.get_children(body[key])
			if not children:
				# Element has no children, move back to previous state and jump out of the loop
				self.grid.move_back()
				continue
			
			keys = self.get_keys(children)
			if keys:
				# Traverse path of children of element
				self.traverse_path_of_robot(children)
		# Parent has no more children, move back to previous state
		self.grid.move_back()	

	def render_robot(self, children, image_path):
		try:
			# Calculate dimensions of drawing and core position
			self.traverse_path_of_robot(children)
			robot_dim = self.grid.calculate_grid_dimensions()
			width = abs(robot_dim[0] - robot_dim[1]) + 1
			height = abs(robot_dim[2] - robot_dim[3]) + 1
			core_position = [width - robot_dim[1] - 1, height - robot_dim[3] - 1]	
			
			# Draw canvas
			cv = Canvas(width, height, 100)
			cv.set_position(core_position[0], core_position[1])
			cv.draw_controller()

			# Draw body of robot
			self.parse_body_to_draw(children, cv)
			
			# Draw sensors after, so that they don't get overdrawn
			cv.draw_sensors()

			cv.save_png(image_path)

			# Reset variables to default values
			cv.reset_canvas()
			self.grid.reset_grid()
			

		except Exception as e: 
			print('Exception {}'.format(e))		