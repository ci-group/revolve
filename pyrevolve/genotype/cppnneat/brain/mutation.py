from typeguard import typechecked

from ..mutation import mutate as cppnneat_mutate
from .config import Config
from .genotype import Genotype


@typechecked
def mutate(genotype: Genotype, config: Config) -> Genotype:
    return cppnneat_mutate(genotype, config)
