from __future__ import annotations

from typing import Any

import multineat
from pyrevolve.genotype import Genotype
from pyrevolve.genotype.bodybrain_composition import BodybrainCompositionConfig
from pyrevolve.revolve_bot import RevolveBot


class BodybrainCompositionGenotype(Genotype):
    _id: int
    _config: BodybrainCompositionConfig
    _body_genotype: Any
    _brain_genotype: Any

    def __init__(
        self,
        robot_id: int,
        config: BodybrainCompositionConfig,
        body_genotype: Any,
        brain_genotype: Any,
    ):
        self._id = robot_id
        self._config = config
        self.body_genotype = body_genotype
        self.brain_genotype = brain_genotype

    def clone(self) -> BodybrainCompositionGenotype:
        return BodybrainCompositionConfig(
            self._id,
            self._config,
            self._body_genotype.clone(),
            self._brain_genotype.clone(),
        )

    def develop(self) -> RevolveBot:
        phenotype = RevolveBot(self._id)
        phenotype._body = self._body.develop().body
        phenotype._brain = self._body.develop().brain
        return phenotype

    @property
    def body_genotype(self) -> Any:
        return self._body_genotype

    @property
    def brain_genotype(self) -> Any:
        return self._brain_genotype
