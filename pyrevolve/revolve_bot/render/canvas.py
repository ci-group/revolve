import cairo
import math

class Canvas:
	# Current position of last drawn element
	x_pos = 0
	y_pos = 0

	# Orientation of robot
	orientation = 1

	# Direction of last movement
	previous_move = -1

	# Coordinates and orientation of movements
	movement_stack = []

	# Positions for the sensors
	sensors = []

	# Rotating orientation in regard to parent module
	rotating_orientation = 0


	def __init__(self, width, height, scale):
		"""Instantiate context and surface"""
		self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width*scale, height*scale)
		context = cairo.Context(self.surface)
		context.scale(scale, scale)
		self.context = context
		self.width = width
		self.height = height
		self.scale = scale


	def get_position(self):
		"""Return current position on x and y axis"""
		return [Canvas.x_pos, Canvas.y_pos]

	def set_position(self, x, y):
		"""Set position of x and y axis"""
		Canvas.x_pos = x
		Canvas.y_pos = y

	def set_orientation(self, orientation):
		"""Set new orientation of robot"""
		if orientation in [0, 1, 2, 3]:
			Canvas.orientation = orientation
		else:
			return False

	def calculate_orientation(self):
		"""Calculate new orientation based on current orientation and last movement direction"""
		if (Canvas.previous_move == -1 or
		(Canvas.previous_move == 1 and Canvas.orientation == 1) or
		(Canvas.previous_move == 2 and Canvas.orientation == 3) or
		(Canvas.previous_move == 3 and Canvas.orientation == 2) or
		(Canvas.previous_move == 0 and Canvas.orientation == 0)):
			self.set_orientation(1)
		elif ((Canvas.previous_move == 2 and Canvas.orientation == 1) or
		(Canvas.previous_move == 0 and Canvas.orientation == 3) or
		(Canvas.previous_move == 1 and Canvas.orientation == 2) or
		(Canvas.previous_move == 3 and Canvas.orientation == 0)):
			self.set_orientation(2)
		elif ((Canvas.previous_move == 0 and Canvas.orientation == 1) or
		(Canvas.previous_move == 3 and Canvas.orientation == 3) or
		(Canvas.previous_move == 2 and Canvas.orientation == 2) or
		(Canvas.previous_move == 1 and Canvas.orientation == 0)):
			self.set_orientation(0)
		elif ((Canvas.previous_move == 3 and Canvas.orientation == 1) or
		(Canvas.previous_move == 1 and Canvas.orientation == 3) or
		(Canvas.previous_move == 0 and Canvas.orientation == 2) or
		(Canvas.previous_move == 2 and Canvas.orientation == 0)):
			self.set_orientation(3)

	def move_by_slot(self, slot):
		"""Move in direction by slot id"""
		if slot == 0:
			self.move_down()
		elif slot == 1:
			self.move_up()
		elif slot == 2:
			self.move_right()
		elif slot == 3:
			self.move_left()

	def move_right(self):
		"""Set position one to the right in correct orientation"""
		if Canvas.orientation == 1:
			Canvas.x_pos += 1
		elif Canvas.orientation == 2:
			Canvas.y_pos += 1
		elif Canvas.orientation == 0:
			Canvas.x_pos -= 1
		elif Canvas.orientation == 3:
			Canvas.y_pos -= 1
		Canvas.previous_move = 2

	def move_left(self):
		"""Set position one to the left"""
		if Canvas.orientation == 1:
			Canvas.x_pos -= 1
		elif Canvas.orientation == 2:
			Canvas.y_pos -= 1
		elif Canvas.orientation == 0:
			Canvas.x_pos += 1
		elif Canvas.orientation == 3:
			Canvas.y_pos += 1
		Canvas.previous_move = 3

	def move_up(self):
		"""Set position one upwards"""
		if Canvas.orientation == 1:
			Canvas.y_pos -= 1
		elif Canvas.orientation == 2:
			Canvas.x_pos += 1
		elif Canvas.orientation == 0:
			Canvas.y_pos += 1
		elif Canvas.orientation == 3:
			Canvas.x_pos -= 1
		Canvas.previous_move = 1

	def move_down(self):
		"""Set position one downwards"""
		if Canvas.orientation == 1:
			Canvas.y_pos += 1
		elif Canvas.orientation == 2:
			Canvas.x_pos -= 1
		elif Canvas.orientation == 0:
			Canvas.y_pos -= 1
		elif Canvas.orientation == 3:
			Canvas.x_pos += 1
		Canvas.previous_move = 0

	def move_back(self):
		"""Move back to previous state on canvas"""
		if len(Canvas.movement_stack) > 1:
			Canvas.movement_stack.pop()
		last_movement = Canvas.movement_stack[-1]
		Canvas.x_pos = last_movement[0]
		Canvas.y_pos = last_movement[1]
		Canvas.orientation = last_movement[2]
		Canvas.rotating_orientation = last_movement[3]

	def sign_id(self, mod_id):
		"""Sign module with the id on the upper left corner of block"""
		self.context.set_font_size(0.3)
		self.context.move_to(Canvas.x_pos, Canvas.y_pos + 0.4)
		self.context.set_source_rgb(0, 0, 0)
		if type(mod_id) is int:
			self.context.show_text(str(mod_id))
		else:
			mod_id = ''.join(x for x in mod_id if x.isdigit())
			self.context.show_text(mod_id)
		self.context.stroke()

	def draw_controller(self, mod_id):
		"""Draw a controller (yellow) in the middle of the canvas"""
		self.context.rectangle(Canvas.x_pos, Canvas.y_pos, 1, 1)
		self.context.set_source_rgb(255, 255, 0)
		self.context.fill_preserve()
		self.context.set_source_rgb(0, 0, 0)
		self.context.set_line_width(0.01)
		self.context.stroke()
		self.sign_id(mod_id)
		Canvas.movement_stack.append([Canvas.x_pos, Canvas.y_pos, Canvas.orientation, Canvas.rotating_orientation])

	def draw_hinge(self, mod_id):
		"""Draw a hinge (blue) on the previous object"""

		self.context.rectangle(Canvas.x_pos, Canvas.y_pos, 1, 1)
		if (Canvas.rotating_orientation % 180 == 0):
			self.context.set_source_rgb(1.0, 0.4, 0.4)
		else:
			self.context.set_source_rgb(1, 0, 0)
		self.context.fill_preserve()
		self.context.set_source_rgb(0, 0, 0)
		self.context.set_line_width(0.01)
		self.context.stroke()
		self.calculate_orientation()
		self.sign_id(mod_id)
		Canvas.movement_stack.append([Canvas.x_pos, Canvas.y_pos, Canvas.orientation, Canvas.rotating_orientation])

	def draw_module(self, mod_id):
		"""Draw a module (red) on the previous object"""
		self.context.rectangle(Canvas.x_pos, Canvas.y_pos, 1, 1)
		self.context.set_source_rgb(0, 0, 1)
		self.context.fill_preserve()
		self.context.set_source_rgb(0, 0, 0)
		self.context.set_line_width(0.01)
		self.context.stroke()
		self.calculate_orientation()
		self.sign_id(mod_id)
		Canvas.movement_stack.append([Canvas.x_pos, Canvas.y_pos, Canvas.orientation, Canvas.rotating_orientation])

	def calculate_sensor_rectangle_position(self):
		"""Calculate squeezed sensor rectangle position based on current orientation and last movement direction"""
		if (Canvas.previous_move == -1 or
		(Canvas.previous_move == 1 and Canvas.orientation == 1) or
		(Canvas.previous_move == 2 and Canvas.orientation == 3) or
		(Canvas.previous_move == 3 and Canvas.orientation == 2) or
		(Canvas.previous_move == 0 and Canvas.orientation == 0)):
			return Canvas.x_pos, Canvas.y_pos + 0.9, 1, 0.1
		elif ((Canvas.previous_move == 2 and Canvas.orientation == 1) or
		(Canvas.previous_move == 0 and Canvas.orientation == 3) or
		(Canvas.previous_move == 1 and Canvas.orientation == 2) or
		(Canvas.previous_move == 3 and Canvas.orientation == 0)):
			return Canvas.x_pos, Canvas.y_pos, 0.1, 1
		elif ((Canvas.previous_move == 0 and Canvas.orientation == 1) or
		(Canvas.previous_move == 3 and Canvas.orientation == 3) or
		(Canvas.previous_move == 2 and Canvas.orientation == 2) or
		(Canvas.previous_move == 1 and Canvas.orientation == 0)):
			return Canvas.x_pos, Canvas.y_pos, 1, 0.1
		elif ((Canvas.previous_move == 3 and Canvas.orientation == 1) or
		(Canvas.previous_move == 1 and Canvas.orientation == 3) or
		(Canvas.previous_move == 0 and Canvas.orientation == 2) or
		(Canvas.previous_move == 2 and Canvas.orientation == 0)):
			return Canvas.x_pos + 0.9, Canvas.y_pos, 0.1, 1

	def save_sensor_position(self):
		"""Save sensor position in list"""
		x, y, x_scale, y_scale = self.calculate_sensor_rectangle_position()
		Canvas.sensors.append([x, y, x_scale, y_scale])
		self.calculate_orientation()
		Canvas.movement_stack.append([Canvas.x_pos, Canvas.y_pos, Canvas.orientation, Canvas.rotating_orientation])

	def draw_sensors(self):
		"""Draw all sensors"""
		for sensor in Canvas.sensors:
			self.context.rectangle(sensor[0], sensor[1], sensor[2], sensor[3])
			self.context.set_source_rgb(0.3, 0.3, 0.3)
			self.context.fill_preserve()
			self.context.set_source_rgb(0, 0, 0)
			self.context.set_line_width(0.01)
			self.context.stroke()

	def calculate_connector_to_parent_position(self):
		"""Calculate position of connector node on canvas"""
		parent = Canvas.movement_stack[-2]
		parent_orientation = parent[2]

		if ((Canvas.previous_move == 1 and parent_orientation == 1) or
		(Canvas.previous_move == 3 and parent_orientation == 2) or
		(Canvas.previous_move == 0 and parent_orientation == 0) or
		(Canvas.previous_move == 2 and parent_orientation == 3)):
			# Connector is on top of parent
			return parent[0] + 0.5, parent[1]
		elif ((Canvas.previous_move == 2 and parent_orientation == 1) or
		(Canvas.previous_move == 1 and parent_orientation == 2) or
		(Canvas.previous_move == 3 and parent_orientation == 0) or
		(Canvas.previous_move == 0 and parent_orientation == 3)):
			# Connector is on right side of parent
			return parent[0] + 1, parent[1] + 0.5
		elif ((Canvas.previous_move == 3 and parent_orientation == 1) or
		(Canvas.previous_move == 0 and parent_orientation == 2) or
		(Canvas.previous_move == 2 and parent_orientation == 0) or
		(Canvas.previous_move == 1 and parent_orientation == 3)):
			# Connector is on left side of parent
			return parent[0], parent[1] + 0.5
		elif ((Canvas.previous_move == 0 and parent_orientation == 1) or
		(Canvas.previous_move == 2 and parent_orientation == 2) or
		(Canvas.previous_move == 1 and parent_orientation == 0) or
		(Canvas.previous_move == 3 and parent_orientation == 3)):
			# Connector is on bottom of parent
			return parent[0] + 0.5, parent[1] + 1

	def draw_connector_to_parent(self):
		"""Draw a circle between child and parent"""
		x, y = self.calculate_connector_to_parent_position()
		self.context.arc(x, y, 0.1, 0, math.pi*2)
		self.context.set_source_rgb(0, 0, 0)
		self.context.fill_preserve()
		self.context.set_source_rgb(0, 0, 0)
		self.context.set_line_width(0.01)
		self.context.stroke()

	def save_png(self, file_name):
		"""Store image representation of canvas"""
		self.surface.write_to_png('%s' % file_name)

	def reset_canvas(self):
		"""Reset canvas variables to default values"""
		Canvas.x_pos = 0
		Canvas.y_pos = 0
		Canvas.orientation = 1
		Canvas.previous_move = -1
		Canvas.movement_stack = []
		Canvas.sensors = []
		Canvas.rotating_orientation = 0
