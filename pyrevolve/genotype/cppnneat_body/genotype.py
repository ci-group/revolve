import multineat
from pyrevolve.genotype.cppnneat.genotype import CppnneatGenotype


class CppnneatBodyGenotype(CppnneatGenotype):
    @staticmethod
    def random(
        multineat_params: multineat.Parameters,
    ) -> CppnneatGenotype:
        n_inputs = 4
        n_outputs = 7
        return super(CppnneatBodyGenotype, CppnneatBodyGenotype).random(
            n_inputs, n_outputs, multineat_params
        )
