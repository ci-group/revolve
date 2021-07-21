from typing import List

from pyrevolve.genotype.bodybrain_composition.config import BodybrainCompositionConfig
from pyrevolve.genotype.bodybrain_composition.genotype import (
    BodybrainCompositionGenotype,
)


def bodybrain_composition_crossover(
    parents: List[BodybrainCompositionGenotype], config: BodybrainCompositionConfig, _
) -> BodybrainCompositionGenotype:
    body_child = config.body_crossover(
        [parent.body_genotype for parent in parents],
        config.body_genotype_config,
        config.body_crossover_config,
    )
    brain_child = config.brain_crossover(
        [parent.brain_genotype for parent in parents],
        config.brain_genotype_config,
        config.brain_crossover_config,
    )
    return BodybrainCompositionGenotype(
        0xDEADBEEF, config, body_child, brain_child
    )  # id is placeholder. expected to be set by framework later
