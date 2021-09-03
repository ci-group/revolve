from typing import List

from typeguard import typechecked

from .config import Config
from .genotype import Genotype


@typechecked
def crossover(parents: List[Genotype], config: Config) -> Genotype:
    assert len(parents) == 2
    return parents[0].mate(
        parents[1],
        config.multineat_params,
        config.rng,
        config.mate_average,
        config.interspecies_crossover,
    )
