class Grid:
	# Current position of last drawn element
	x_pos = 0
	y_pos = 0
	
	# Orientation of robot
	orientation = 1
	
	# Direction of last movement
	previous_move = -1
	
	# Coordinates and orientation of movements
	movement_stack = [[0,0,1]]

	# Coordinates of visited positions
	visited_coordinates = []

	def get_position(self):
		"""Return current position on x and y axis"""
		return [Grid.x_pos, Grid.y_pos]

	def set_position(self, x, y):
		"""Set position of x and y axis"""		
		Grid.x_pos = x
		Grid.y_pos = y
	
	def set_orientation(self, orientation):
		"""Set new orientation on grid"""
		if orientation in [0, 1, 2, 3]:
			Grid.orientation = orientation
		else:
			return False

	def calculate_orientation(self):
		"""Set orientation by previous move and orientation"""
		if (Grid.previous_move == -1 or
		(Grid.previous_move == 1 and Grid.orientation == 1) or
		(Grid.previous_move == 2 and Grid.orientation == 3) or
		(Grid.previous_move == 3 and Grid.orientation == 2) or
		(Grid.previous_move == 0 and Grid.orientation == 0)):
			self.set_orientation(1)
		elif ((Grid.previous_move == 2 and Grid.orientation == 1) or
		(Grid.previous_move == 0 and Grid.orientation == 3) or
		(Grid.previous_move == 1 and Grid.orientation == 2) or
		(Grid.previous_move == 3 and Grid.orientation == 0)):
			self.set_orientation(2)
		elif ((Grid.previous_move == 0 and Grid.orientation == 1) or
		(Grid.previous_move == 3 and Grid.orientation == 3) or
		(Grid.previous_move == 2 and Grid.orientation == 2) or
		(Grid.previous_move == 1 and Grid.orientation == 0)):
			self.set_orientation(0)	
		elif ((Grid.previous_move == 3 and Grid.orientation == 1) or
		(Grid.previous_move == 1 and Grid.orientation == 3) or
		(Grid.previous_move == 0 and Grid.orientation == 2) or
		(Grid.previous_move == 2 and Grid.orientation == 0)):
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
		if Grid.orientation == 1:
			Grid.x_pos += 1
		elif Grid.orientation == 2:
			Grid.y_pos += 1
		elif Grid.orientation == 0:
			Grid.x_pos -= 1
		elif Grid.orientation == 3:
			Grid.y_pos -= 1
		Grid.previous_move = 2
		
	def move_left(self):
		"""Set position one to the left"""
		if Grid.orientation == 1:
			Grid.x_pos -= 1		
		elif Grid.orientation == 2:
			Grid.y_pos -= 1
		elif Grid.orientation == 0:
			Grid.x_pos += 1
		elif Grid.orientation == 3:
			Grid.y_pos += 1
		Grid.previous_move = 3
			
	def move_up(self):
		"""Set position one upwards"""
		if Grid.orientation == 1:
			Grid.y_pos -= 1
		elif Grid.orientation == 2:
			Grid.x_pos += 1
		elif Grid.orientation == 0:
			Grid.y_pos += 1
		elif Grid.orientation == 3:
			Grid.x_pos -= 1	
		Grid.previous_move = 1
			
	def move_down(self):
		"""Set position one downwards"""
		if Grid.orientation == 1:
			Grid.y_pos += 1
		elif Grid.orientation == 2:
			Grid.x_pos -= 1
		elif Grid.orientation == 0:
			Grid.y_pos -= 1
		elif Grid.orientation == 3:
			Grid.x_pos += 1	
		Grid.previous_move = 0
			
	def move_back(self):
		if len(Grid.movement_stack) > 1:
			Grid.movement_stack.pop()	
		last_movement = Grid.movement_stack[-1]
		Grid.x_pos = last_movement[0]
		Grid.y_pos = last_movement[1]
		Grid.orientation = last_movement[2]				

	def add_to_visited(self):
		"""Add current position to visited coordinates list"""
		self.calculate_orientation()
		Grid.visited_coordinates.append([Grid.x_pos, Grid.y_pos])
		Grid.movement_stack.append([Grid.x_pos, Grid.y_pos, Grid.orientation])

	def calculate_grid_dimensions(self):
		min_x = 0
		max_x = 0
		min_y = 0
		max_y = 0
		for coorinate in Grid.visited_coordinates:
			min_x = coorinate[0] if coorinate[0] < min_x else min_x
			max_x = coorinate[0] if coorinate[0] > max_x else max_x
			min_y = coorinate[1] if coorinate[1] < min_y else min_y
			max_y = coorinate[1] if coorinate[1] > max_y else max_y
		return [min_x, max_x, min_y, max_y]

	def reset_grid(self):
		Grid.x_pos = 0
		Grid.y_pos = 0
		Grid.orientation = 1
		Grid.previous_move = -1
		Grid.movement_stack = [[0,0,1]]
		Grid.visited_coordinates = []