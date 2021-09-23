from __future__ import annotations

from typing import Any, Dict, List

from typeguard import typechecked

from ..bodybrain_composition.sub_genotype import \
    SubGenotype as BodybrainCompositionSubGenotype
from ..direct_tree.direct_tree_genotype import DirectTreeGenotype



class Genotype(BodybrainCompositionSubGenotype):
    genotype_impl: DirectTreeGenotype

    def __init__(self, genotype_impl: DirectTreeGenotype):
        self.genotype_impl = genotype_impl

    def serialize_to_dict(self) -> Dict[Any, Any]:
        self.genotype_impl.develop()
        return self.genotype_impl.phenotype.to_yaml()

    def deserialize_from_dict(self, serialized: Dict[Any, Any]):
        self = serialized

    @staticmethod
    @typechecked
    def random(conf) -> Genotype:

        gen = DirectTreeGenotype(conf.body_dtree_config, 0).random_initialization()
        out = Genotype(genotype_impl=gen)
        return out

    @typechecked
    def clone(self) -> Genotype:
        return Genotype(self.genotype_impl)

