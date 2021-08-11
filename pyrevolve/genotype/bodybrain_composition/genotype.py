from __future__ import annotations

import json
import typing
from typing import Generic, TypeVar

from pyrevolve.genotype import Genotype
from pyrevolve.genotype.bodybrain_composition.config import BodybrainCompositionConfig
from pyrevolve.revolve_bot import RevolveBot

_body_type = TypeVar("_body_type")
_brain_type = TypeVar("_brain_type")


class BodybrainCompositionGenotype(Generic[_body_type, _brain_type], Genotype):
    id: int
    _config: BodybrainCompositionConfig
    _body_genotype: _body_type
    _brain_genotype: _brain_type

    def __init__(
        self,
        robot_id: int,
        config: BodybrainCompositionConfig,
        body_genotype: _body_type,
        brain_genotype: _brain_type,
    ):
        self.id = robot_id
        self._config = config
        self._body_genotype = body_genotype
        self._brain_genotype = brain_genotype

    def develop(self) -> RevolveBot:
        phenotype = RevolveBot(self.id)
        phenotype._body = self._config.body_develop(
            self._body_genotype, self._config.body_develop_config
        )
        phenotype._brain = self._config.brain_develop(
            self._brain_genotype, self._config.brain_develop_config, phenotype._body
        )
        phenotype.update_substrate()
        return phenotype

    def export_genotype(self, filepath: str):
        body = self._body_genotype.serialize_to_dict()
        brain = self._brain_genotype.serialize_to_dict()
        asjson = json.dumps({"body": body, "brain": brain})
        file = open(filepath, "w+")
        file.write(asjson)
        file.close()

    def load_genotype(self, filepath: str) -> None:
        file = open(filepath)
        data = json.loads(file.read())
        self._body_genotype = type(self._body_genotype).deserialize_from_dict(
            data["body"]
        )
        self._brain_genotype = type(self._brain_genotype).deserialize_from_dict(
            data["brain"]
        )

    @property
    def body_genotype(self) -> _body_type:
        return self._body_genotype

    @property
    def brain_genotype(self) -> _brain_type:
        return self._brain_genotype
