from typing import List

from pyrevolve.evolution.individual import Individual
from typeguard import typechecked

from .config import Config
from .genotype import Genotype


@typechecked
def crossover(parents: List[Individual], _, config: Config) -> Genotype:
    assert len(parents) >= 1

    body_genotype_type = type(parents[0].body_genotype)
    brain_genotype_type = type(parents[0].brain_genotype)

    # assert all parents' body genotypes are of the same type
    # same for brain genotypes
    assert all([type(parent.body_genotype) == body_genotype_type for parent in parents])
    assert all(
        [type(parent.brain_genotype) == brain_genotype_type for parent in parents]
    )

    body_child = config.body_crossover(
        [parent.genotype.body_genotype for parent in parents],
        config.body_crossover_config,
    )
    assert type(body_child) == body_genotype_type

    brain_child = config.brain_crossover(
        [parent.genotype.brain_genotype for parent in parents],
        config.brain_crossover_config,
    )
    assert type(brain_child) == brain_genotype_type

    return Genotype(
        0xDEADBEEF, config, body_child, brain_child
    )  # id is placeholder. expected to be set by framework later
