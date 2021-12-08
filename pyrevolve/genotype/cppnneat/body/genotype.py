from __future__ import annotations

import multineat
from typeguard import typechecked

from ..genotype import Genotype as CppnneatGenotype
from pyrevolve.genotype.cppnneat.config import Config


class Genotype(CppnneatGenotype):
    linearactuator = Config.linearactuator
    n_output = None

    @staticmethod
    @typechecked
    def random(
        multineat_params: multineat.Parameters,
        output_activation_type: multineat.ActivationFunction,
        n_start_mutations: int,
        innov_db: multineat.InnovationDatabase,
        rng: multineat.RNG,
    ) -> Genotype:
        if Genotype.linearactuator:
            Genotype.n_output = 6
        else:
            Genotype.n_output = 5
        n_inputs = 4 + 1  # bias(always 1), pos_x, pos_y, pos_z, chain_length
        random_parent = super(Genotype, Genotype).random(
            n_inputs,
            Genotype.n_output,
            multineat_params,
            output_activation_type,
            n_start_mutations,
            innov_db,
            rng,
        )

        return Genotype(random_parent._multineat_genome)
