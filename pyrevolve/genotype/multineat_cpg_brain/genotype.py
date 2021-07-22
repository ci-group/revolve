import multineat
from pyrevolve.genotype.neatcppn.genotype import NeatcppnGenotype


class MultineatCpgBrainGenotype(NeatcppnGenotype):
    @staticmethod
    def random(
        multineat_params: multineat.Parameters,
    ) -> NeatcppnGenotype:
        n_inputs = 4
        n_outputs = 1
        return super(MultineatCpgBrainGenotype, MultineatCpgBrainGenotype).random(
            n_inputs, n_outputs, multineat_params
        )
