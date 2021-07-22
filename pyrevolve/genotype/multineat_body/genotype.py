import multineat
from pyrevolve.genotype.multineat.genotype import MultineatGenotype


class MultineatBodyGenotype(MultineatGenotype):
    @staticmethod
    def random(
        multineat_params: multineat.Parameters,
    ) -> MultineatGenotype:
        n_inputs = 4
        n_outputs = 6
        return super(MultineatBodyGenotype, MultineatBodyGenotype).random(
            n_inputs, n_outputs, multineat_params
        )
