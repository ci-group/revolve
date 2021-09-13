from __future__ import annotations

from typing import Dict, Any, List

from typeguard import typechecked

from ..plasticoding.initialization import _generate_random_grammar
from ..plasticoding.plasticoding import Alphabet
from ..bodybrain_composition.sub_genotype import (
    SubGenotype as BodybrainCompositionSubGenotype,
)

class Genotype(BodybrainCompositionSubGenotype):
    genotype_impl: Dict[Alphabet, List[Any]]

    def __init__(self, genotype_impl: dict):
        self.genotype_impl = genotype_impl

    def serialize_to_dict(self) -> Dict[Any, Any]:
        return self.genotype_impl

    def deserialize_from_dict(self, serialized: Dict[str, Any]):
        self.genotype_impl = serialized

    @staticmethod
    @typechecked
    def random(conf) -> Genotype:
        gen = Genotype(genotype_impl=_generate_random_grammar(conf))
        return gen


