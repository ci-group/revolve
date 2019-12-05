class Genotype:
    def clone(self):
        """
        Create an returns deep copy of the genotype
        """
        raise NotImplementedError("Method must be implemented by genome")

    def develop(self, environment):
        """
        Develops the genome into a revolve_bot (proto-phenotype)

        :return: a RevolveBot instance
        :rtype: RevolveBot
        """
        raise NotImplementedError("Method must be implemented by genome")


class GenotypeConfig:
    def __init__(self,
                 e_max_groups,
                 axiom_w,
                 i_iterations,
                 weight_min,
                 weight_max,
                 oscillator_param_min,
                 oscillator_param_max,
                 max_clauses,
                 max_terms_clause,
                 plastic,
                 environmental_conditions,
                 logic_operators):
        self.e_max_groups = e_max_groups
        self.axiom_w = axiom_w
        self.i_iterations = i_iterations
        self.weight_min = weight_min
        self.weight_max = weight_max
        self.oscillator_param_min = oscillator_param_min
        self.oscillator_param_max = oscillator_param_max
        self.max_clauses = max_clauses
        self.max_terms_clause = max_terms_clause
        self.plastic = plastic
        self.environmental_conditions = environmental_conditions
        self.logic_operators = logic_operators
