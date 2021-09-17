from typing import List

from typeguard import typechecked

from ..crossover import crossover as cppnneat_crossover
from .config import Config
from .genotype import Genotype


@typechecked
def crossover(parents: List[Genotype], config: Config) -> Genotype:
    crossover_parent = cppnneat_crossover(parents, config)
    return Genotype(crossover_parent._multineat_genome)
