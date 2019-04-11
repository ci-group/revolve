class CrossoverConfig:
	def __init__(self,
		crossover_prob):
		"""
		Creates a Crossover object that sets the configuration for the crossover operator

		:param crossover_prob: crossover probability
		"""
		self.crossover_prob = crossover_prob