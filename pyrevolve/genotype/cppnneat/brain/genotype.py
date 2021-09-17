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
        n_inputs = 6 + 1  # bias(always 1), x1, y1, z1, x2, y2, z2
        n_outputs = 1  # weight
        random_parent = super(Genotype, Genotype).random(
            n_inputs,
            n_outputs,
            multineat_params,
            output_activation_type,
            n_start_mutations,
            innov_db,
            rng,
        )
        return Genotype(random_parent._multineat_genome)
