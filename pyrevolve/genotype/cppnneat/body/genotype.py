from __future__ import annotations

import multineat
from typeguard import typechecked

from ..genotype import Genotype as CppnneatGenotype


class Genotype(CppnneatGenotype):
    @staticmethod
    @typechecked
    def random(
        multineat_params: multineat.Parameters,
        output_activation_type: multineat.ActivationFunction,
        n_start_mutations: int,
        innov_db: multineat.InnovationDatabase,
        rng: multineat.RNG,
    ) -> Genotype:
        n_inputs = 4 + 1  # bias(always 1), pos_x, pos_y, pos_z, chain_length
        n_outputs = 5  # empty, brick, activehinge, rot0, rot90
        random_parent = super(Genotype, Genotype).random(
            n_inputs,
            n_outputs,
            multineat_params,
            output_activation_type,
            n_start_mutations,
            innov_db,
            rng,
        )
        asd = Genotype(random_parent._multineat_genome)
        print(type(asd))
        return asd
