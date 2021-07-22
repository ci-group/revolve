from __future__ import annotations

from typing import Any

from pyrevolve.genotype import Genotype
from pyrevolve.genotype.bodybrain_composition.config import \
    BodybrainCompositionConfig
from pyrevolve.revolve_bot import RevolveBot


class BodybrainCompositionGenotype(Genotype):
    id: int
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
        self.id = robot_id
        self._config = config
        self._body_genotype = body_genotype
        self._brain_genotype = brain_genotype

    def develop(self) -> RevolveBot:
        phenotype = RevolveBot("robot_" + str(self.id))
        phenotype._body = self._config.body_develop(
            self._body_genotype, self._config.body_develop_config
        )
        phenotype._brain = self._config.brain_develop(
            self._brain_genotype, self._config.brain_develop_config
        )
        return phenotype

    def export_genotype(self, filepath):
        file = open(filepath, "w+")
        file.write("placeholder genotype export" + "\n")
        file.close()

    @property
    def body_genotype(self) -> Any:
        return self._body_genotype

    @property
    def brain_genotype(self) -> Any:
        return self._brain_genotype
