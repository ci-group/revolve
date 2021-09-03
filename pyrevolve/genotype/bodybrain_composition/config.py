from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Generic, List, TypeVar

from pyrevolve.revolve_bot.brain import Brain
from pyrevolve.revolve_bot.revolve_module import CoreModule

from .sub_genotype import SubGenotype

_body_genotype = TypeVar("_body_genotype", bound=SubGenotype)
_body_crossover_config = TypeVar("_body_crossover_config")
_body_mutate_config = TypeVar("_body_mutate_config")
_body_develop_config = TypeVar("_body_develop_config")
_brain_genotype = TypeVar("_brain_genotype", bound=SubGenotype)
_brain_crossover_config = TypeVar("_brain_crossover_config")
_brain_mutate_config = TypeVar("_brain_mutate_config")
_brain_develop_config = TypeVar("_brain_develop_config")


@dataclass(frozen=True)
class Config(
    Generic[
        _body_genotype,
        _body_crossover_config,
        _body_mutate_config,
        _body_develop_config,
        _brain_genotype,
        _brain_crossover_config,
        _brain_mutate_config,
        _brain_develop_config,
    ]
):
    body_crossover: Callable[
        [
            List[_body_genotype],
            _body_crossover_config,
        ],
        _body_genotype,
    ]
    body_crossover_config: _body_crossover_config
    body_mutate: Callable[[_body_genotype, _body_mutate_config], _body_genotype]
    body_mutate_config: _body_mutate_config
    body_develop: Callable[[_body_genotype, _brain_develop_config], CoreModule]
    body_develop_config: _body_develop_config

    brain_crossover: Callable[
        [
            List[_brain_genotype],
            _brain_crossover_config,
        ],
        _brain_genotype,
    ]
    brain_crossover_config: _brain_crossover_config
    brain_mutate: Callable[[_brain_genotype, _brain_mutate_config], _brain_genotype]
    brain_mutate_config: _brain_mutate_config
    brain_develop: Callable[[_brain_genotype, _brain_develop_config, CoreModule], Brain]
    brain_develop_config: _brain_develop_config
