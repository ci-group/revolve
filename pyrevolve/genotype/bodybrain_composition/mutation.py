from pyrevolve.genotype.bodybrain_composition.config import BodybrainCompositionConfig
from pyrevolve.genotype.bodybrain_composition.genotype import (
    BodybrainCompositionGenotype,
)


def bodybrain_composition_mutate(
    genotype: BodybrainCompositionGenotype, config: BodybrainCompositionConfig
) -> BodybrainCompositionGenotype:
    mutated_body = config.body_mutate(genotype.body_genotype, config.body_mutate_config)
    mutated_brain = config.brain_mutate(
        genotype.brain_genotype, config.brain_mutate_config
    )
    return BodybrainCompositionGenotype(
        0xCAFED00D, config, mutated_body, mutated_brain
    )  # id is placeholder. expected to be set by framework later
