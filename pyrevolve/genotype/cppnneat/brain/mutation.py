from typeguard import typechecked

from ..mutation import mutate as cppnneat_mutate
from .config import Config
from .genotype import Genotype


@typechecked
def mutate(genotype: Genotype, config: Config) -> Genotype:
    parent_mutate = cppnneat_mutate(genotype, config)
    return Genotype(parent_mutate._multineat_genome)
