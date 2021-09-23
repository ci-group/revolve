from __future__ import annotations

from typing import Any, Dict, List

from typeguard import typechecked

from ..bodybrain_composition.sub_genotype import \
    SubGenotype as BodybrainCompositionSubGenotype


class Genotype(BodybrainCompositionSubGenotype):

    def serialize_to_dict(self) -> Dict[Any, Any]:
        return str(self)

    def deserialize_from_dict(self, serialized: Dict[Any, Any]):
        pass

    @staticmethod
    @typechecked
    def random(conf):
        #pass
        gen = Genotype()
        return gen
