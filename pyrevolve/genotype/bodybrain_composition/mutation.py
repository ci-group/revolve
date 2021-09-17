from typeguard import typechecked

from .config import Config
from .genotype import Genotype


@typechecked
def mutate(genotype: Genotype, config: Config) -> Genotype:
    mutated_body = config.body_mutate(genotype.body_genotype, config.body_mutate_config)
    assert type(mutated_body) == type(genotype.body_genotype)

    mutated_brain = config.brain_mutate(
        genotype.brain_genotype, config.brain_mutate_config
    )
    assert type(mutated_brain) == type(genotype.brain_genotype)

    return Genotype(
        genotype.id, config, mutated_body, mutated_brain
    )  # id must be the same as input id
