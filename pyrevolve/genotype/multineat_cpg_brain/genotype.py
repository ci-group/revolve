import multineat
from pyrevolve.genotype.multineat.genotype import MultineatGenotype


class MultineatCpgBrainGenotype(MultineatGenotype):
    @staticmethod
    def random(
        multineat_params: multineat.Parameters,
    ) -> MultineatGenotype:
        n_inputs = 4
        n_outputs = 1
        return super(MultineatCpgBrainGenotype, MultineatCpgBrainGenotype).random(
            n_inputs, n_outputs, multineat_params
        )
