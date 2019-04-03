
class Genotype:

    def __init__(self):
        self.id = None
        self.representation = None

class GenotypeConfig:
	def __init__(self,
		e_max_groups,
		axiom_w,
		i_iterations,
		weight_min,
		weight_max,
		oscillator_param_min,
		oscillator_param_max):

		self.e_max_groups = e_max_groups
		self.axiom_w = axiom_w
		self.i_iterations = i_iterations
		self.weight_min = weight_min
		self.weight_max = weight_max
		self.oscillator_param_min = oscillator_param_min
		self.oscillator_param_max = oscillator_param_max