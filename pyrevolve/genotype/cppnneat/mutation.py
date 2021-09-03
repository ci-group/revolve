from typeguard import typechecked

from .config import Config
from .genotype import Genotype


@typechecked
def mutate(genotype: Genotype, config: Config) -> Genotype:
    copy = genotype.clone()
    copy.mutate(config.multineat_params, config.innov_db, config.rng)
    return copy
