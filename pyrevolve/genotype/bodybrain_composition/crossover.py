from typing import List

from pyrevolve.evolution.individual import Individual
from pyrevolve.genotype.bodybrain_composition.config import BodybrainCompositionConfig
from pyrevolve.genotype.bodybrain_composition.genotype import (
    BodybrainCompositionGenotype,
)


def bodybrain_composition_crossover(
    parents: List[Individual], _, config: BodybrainCompositionConfig
) -> BodybrainCompositionGenotype:
    body_child = config.body_crossover(
        [parent.genotype.body_genotype for parent in parents],
        config.body_crossover_config,
    )
    brain_child = config.brain_crossover(
        [parent.genotype.brain_genotype for parent in parents],
        config.brain_crossover_config,
    )
    return BodybrainCompositionGenotype(
        0xDEADBEEF, config, body_child, brain_child
    )  # id is placeholder. expected to be set by framework later
