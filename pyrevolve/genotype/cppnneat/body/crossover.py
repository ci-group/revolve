from typing import List

from typeguard import typechecked

from ..crossover import crossover as cppnneat_crossover
from .config import Config
from .genotype import Genotype


@typechecked
def crossover(parents: List[Genotype], config: Config) -> Genotype:
    return cppnneat_crossover(parents, config)
