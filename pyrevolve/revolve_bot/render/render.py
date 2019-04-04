import cairo
from .canvas import Canvas
from .grid import Grid
from ..revolve_module import RevolveModule, CoreModule, BrickModule, ActiveHingeModule, TouchSensorModule, BrickSensorModule

class Render:

	def __init__(self):
		"""Instantiate grid"""
		self.grid = Grid()

	def parse_body_to_draw(self, canvas, module, slot):
		"""
		Parse the body to the canvas to draw the png
		@param canvas: instance of the Canvas class
		@param module: body of the robot
		@param slot: parent slot of module
		"""
		if isinstance(module, CoreModule):
			canvas.draw_controller()
		elif isinstance(module, ActiveHingeModule):
			canvas.move_by_slot(slot)
			Canvas.rotating_orientation += module.orientation
			canvas.draw_hinge(module.id)
			canvas.draw_connector_to_parent()
		elif isinstance(module, BrickModule):
			canvas.move_by_slot(slot)
			Canvas.rotating_orientation += module.orientation
			canvas.draw_module(module.id)
			canvas.draw_connector_to_parent()
		elif isinstance(module, TouchSensorModule) or isinstance(module, BrickSensorModule):
			canvas.move_by_slot(slot)
			Canvas.rotating_orientation += module.orientation
			canvas.save_sensor_position()

		if module.has_children():
			# Traverse children of element to draw on canvas
			for core_slot, child_module in module.iter_children():
				if child_module is None:
					continue
				self.parse_body_to_draw(canvas, child_module, core_slot)
			canvas.move_back()
		else:
			# Element has no children, move back to previous state
			canvas.move_back()

	def traverse_path_of_robot(self, module, slot, include_sensors=True):
		"""
		Traverse path of robot to obtain visited coordinates
		@param module: body of the robot
		@param slot: attachment of parent slot
		@param include_sensors: add sensors to visisted_cooridnates if True
		"""
		if isinstance(module, ActiveHingeModule) or isinstance(module, BrickModule) or isinstance(module, TouchSensorModule) or isinstance(module, BrickSensorModule):
			self.grid.move_by_slot(slot)
			self.grid.add_to_visited(include_sensors, isinstance(module, TouchSensorModule))
		if module.has_children():
			# Traverse path of children of module
			for core_slot, child_module in module.iter_children():
				if child_module is None:
					continue
				self.traverse_path_of_robot(child_module, core_slot, include_sensors)
			self.grid.move_back()
		else:
			# Element has no children, move back to previous state
			self.grid.move_back()

	def render_robot(self, body, image_path):
		"""
		Render robot and save image file
		@param body: body of robot
		@param image_path: file path for saving image
		"""
		try:
			# Calculate dimensions of drawing and core position
			self.traverse_path_of_robot(body, 0)
			self.grid.calculate_grid_dimensions()
			core_position = self.grid.calculate_core_position()

			# Draw canvas
			cv = Canvas(self.grid.width, self.grid.height, 100)
			cv.set_position(core_position[0], core_position[1])

			# Draw body of robot
			self.parse_body_to_draw(cv, body, 0)

			# Draw sensors after, so that they don't get overdrawn
			cv.draw_sensors()

			cv.save_png(image_path)

			# Reset variables to default values
			cv.reset_canvas()
			self.grid.reset_grid()

		except Exception as e:
			print('Exception {}'.format(e))
