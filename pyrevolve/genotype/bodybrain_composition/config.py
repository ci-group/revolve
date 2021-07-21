from dataclasses import dataclass
from typing import Any, Callable, List


@dataclass
class BodybrainCompositionConfig:
    body_genotype_config: Any
    brain_genotype_config: Any
    body_crossover: Callable[
        [
            List[Any],
            Any,
            Any,
        ],
        Any,
    ]
    brain_crossover: Callable[
        [
            List[Any],
            Any,
            Any,
        ],
        Any,
    ]
    body_crossover_config: Any
    brain_crossover_config: Any
    body_mutate: Callable[[Any, Any], Any]
    brain_mutate: Callable[[Any, Any], Any]
    body_mutate_config: Any
    brain_mutate_config: Any
