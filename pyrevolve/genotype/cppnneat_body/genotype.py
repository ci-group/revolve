import multineat
from pyrevolve.genotype.cppnneat.genotype import CppnneatGenotype


class CppnneatBodyGenotype(CppnneatGenotype):
    @staticmethod
    def random(
        multineat_params: multineat.Parameters,
        n_start_mutations: int,
        innov_db: multineat.InnovationDatabase,
        rng: multineat.RNG,
    ) -> CppnneatGenotype:
        n_inputs = 4 + 1  # 1 extra for bias
        n_outputs = 5 # empty, brick, activehinge, rot0, rot90
        return super(CppnneatBodyGenotype, CppnneatBodyGenotype).random(
            n_inputs, n_outputs, multineat_params, n_start_mutations, innov_db, rng
        )
