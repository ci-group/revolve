from __future__ import annotations

from typing import Any, Dict

import multineat
from typeguard import typechecked

from ..bodybrain_composition.sub_genotype import (
    SubGenotype as BodybrainCompositionSubGenotype,
)


class Genotype(BodybrainCompositionSubGenotype):
    _multineat_genome: multineat.Genomemultineat_genome

    @typechecked
    def __init__(self, multineat_genome: multineat.Genome):
        self._multineat_genome = multineat_genome

    @staticmethod
    @typechecked
    def random(
        n_inputs: int,
        n_outputs: int,
        multineat_params: multineat.Parameters,
        output_activation_type: multineat.ActivationFunction,
        n_start_mutations: int,
        innov_db: multineat.InnovationDatabase,
        rng: multineat.RNG,
    ) -> Genotype:
        multineat_genome = multineat.Genome(
            0,  # ID
            n_inputs,
            0,  # n_hidden
            n_outputs,
            False,  # FS_NEAT
            output_activation_type,
            multineat.ActivationFunction.TANH,  # hidden activation type
            0,  # seed_type
            multineat_params,
            0,  # number of hidden layers
        )

        genome = Genotype(multineat_genome)
        for _ in range(n_start_mutations):
            genome.mutate(multineat_params, innov_db, rng)

        return genome

    @property
    @typechecked
    def multineat_genome(self) -> multineat.Genome:
        return self._multineat_genome

    @typechecked
    def mutate(
        self,
        multineat_params: multineat.Parameters,
        innov_db: multineat.InnovationDatabase,
        rng: multineat.RNG,
    ) -> None:
        self.multineat_genome.Mutate(
            False,
            multineat.SearchMode.COMPLEXIFYING,
            innov_db,
            multineat_params,
            rng,
        )

    @typechecked
    def mate(
        self,
        partner: Genotype,
        multineat_params: multineat.Parameters,
        rng: multineat.RNG,
        mate_average: bool,
        interspecies_crossover: bool,
    ) -> Genotype:
        child_multineat_genome = self.multineat_genome.Mate(
            partner.multineat_genome,
            mate_average,
            interspecies_crossover,
            rng,
            multineat_params,
        )
        return Genotype(child_multineat_genome)

    @typechecked
    def clone(self) -> Genotype:
        return Genotype(multineat.Genome(self.multineat_genome))

    @typechecked
    def serialize_to_dict(self) -> Dict[str, Any]:
        return {"multineat_genome": self._multineat_genome.Serialize()}

    @typechecked
    def deserialize_from_dict(self, serialized: Dict[str, Any]):
        self._multineat_genome.Deserialize(serialized["multineat_genome"])
