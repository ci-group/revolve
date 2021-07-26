import multineat
from pyrevolve.genotype.cppnneat.genotype import CppnneatGenotype


class CppnneatCpgBrainGenotype(CppnneatGenotype):
    @staticmethod
    def random(
        multineat_params: multineat.Parameters,
        n_start_mutations: int,
        innov_db: multineat.InnovationDatabase,
        rng: multineat.RNG,
    ) -> CppnneatGenotype:
        n_inputs = 6
        n_outputs = 1
        return super(CppnneatCpgBrainGenotype, CppnneatCpgBrainGenotype).random(
            n_inputs, n_outputs, multineat_params, n_start_mutations, innov_db, rng
        )
