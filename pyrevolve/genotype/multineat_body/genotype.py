import multineat
from pyrevolve.genotype.neatcppn.genotype import NeatcppnGenotype


class MultineatBodyGenotype(NeatcppnGenotype):
    @staticmethod
    def random(
        multineat_params: multineat.Parameters,
    ) -> NeatcppnGenotype:
        n_inputs = 4
        n_outputs = 6
        return super(MultineatBodyGenotype, MultineatBodyGenotype).random(
            n_inputs, n_outputs, multineat_params
        )
