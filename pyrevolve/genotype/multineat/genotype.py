from __future__ import annotations

import multineat
from pyrevolve.revolve_bot import RevolveBot


class MultineatGenotype:
    _multineat_genome: multineat.Genome

    def __init__(self, multineat_genome: multineat.Genome):
        self._multineat_genome = multineat_genome

    @staticmethod
    def random(
        n_inputs: int,
        n_outputs: int,
        multineat_params: multineat.Parameters,
    ) -> MultineatGenotype:
        multineat_genome = multineat.Genome(
            0,  # ID
            n_inputs,
            0,  # n_hidden
            n_outputs,
            False,  # FS_NEAT
            multineat.ActivationFunction.TANH,  # output activation type
            multineat.ActivationFunction.TANH,  # hidden activation type
            0,  # seed_type
            multineat_params,
            0,  # number of hidden layers
        )
        return MultineatGenotype(multineat_genome)
