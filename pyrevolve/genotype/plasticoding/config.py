from pyrevolve.genotype.plasticoding import initialization
from pyrevolve.genotype.plasticoding.plasticoding import Alphabet

class PlasticodingConfig:
    def __init__(self,
                 initialization_genome=initialization.random_initialization,
                 e_max_groups=4,
                 oscillator_param_min=1,
                 oscillator_param_max=10,
                 weight_param_min=-1,
                 weight_param_max=1,
                 weight_min=-1,
                 weight_max=1,
                 axiom_w=Alphabet.CORE_COMPONENT,
                 i_iterations=3,
                 max_structural_modules=15,
                 robot_id=0,
                 move_to_new=False,
                 max_clauses=2,
                 max_terms_clause=2,
                 plastic=False,
                 environmental_conditions=['hill'],
                 logic_operators=['and', 'or']
                 ):
        self.initialization_genome = initialization_genome
        self.e_max_groups = e_max_groups
        self.oscillator_param_min = oscillator_param_min
        self.oscillator_param_max = oscillator_param_max
        self.weight_param_min = weight_param_min
        self.weight_param_max = weight_param_max
        self.weight_min = weight_min
        self.weight_max = weight_max
        self.axiom_w = axiom_w
        self.i_iterations = i_iterations
        self.max_structural_modules = max_structural_modules
        self.robot_id = robot_id
        self.move_to_new = move_to_new
        self.max_clauses = max_clauses
        self.max_terms_clause = max_terms_clause
        self.plastic = plastic
        self.environmental_conditions = environmental_conditions
        self.logic_operators = logic_operators
