import copy


class Genotype:
    def clone(self):
        """
        Create an returns deep copy of the genotype
        """
        return copy.deepcopy(self)

    def develop(self):
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
                 oscillator_param_max):
        self.e_max_groups = e_max_groups
        self.axiom_w = axiom_w
        self.i_iterations = i_iterations
        self.weight_min = weight_min
        self.weight_max = weight_max
        self.oscillator_param_min = oscillator_param_min
        self.oscillator_param_max = oscillator_param_max
