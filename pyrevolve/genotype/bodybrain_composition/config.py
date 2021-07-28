from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, List

from pyrevolve.evolution.individual import Individual
from pyrevolve.revolve_bot.brain import Brain
from pyrevolve.revolve_bot.revolve_module import CoreModule


@dataclass
class BodybrainCompositionConfig:
    body_crossover: Callable[
        [
            List[Any],
            Any,
        ],
        Any,
    ]  # ([parents: body_genotype], body_crossover_config) -> body_genotype
    brain_crossover: Callable[
        [
            List[Any],
            Any,
        ],
        Any,
    ]  # see body_crossover
    body_crossover_config: Any
    brain_crossover_config: Any
    body_mutate: Callable[
        [Any, Any], Any
    ]  # (body_genotype, body_mutate_config) -> body_genotype
    brain_mutate: Callable[[Any, Any], Any]  # see body_mutate
    body_mutate_config: Any
    brain_mutate_config: Any
    body_develop: Callable[
        [Any, Any], CoreModule
    ]  # (body_genotype, body_develop_config) -> CoreModule
    brain_develop: Callable[
        [Any, Any, CoreModule], Brain
    ]  # (brain_genotype, brain_develop_config) -> Brain
    body_develop_config: Any
    brain_develop_config: Any
