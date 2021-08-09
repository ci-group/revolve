from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Dict


class Age:

    def __init__(self):
        # Age of the species (in generations)
        self._generations: int = 0
        # Age of the species (in evaluations)
        self._evaluations: int = 0

        # generational counter.
        self._no_improvements: int = 0

    def __eq__(self, other):
        if not isinstance(other, Age):
            # don't attempt to compare against unrelated types
            return NotImplemented

        return self._generations == other._generations \
            and self._evaluations == other._evaluations \
            and self._no_improvements == other._no_improvements

    # GETTERS
    def generations(self):
        return self._generations

    def evaluations(self):
        return self._evaluations

    def no_improvements(self):
        return self._no_improvements

    # Age
    def increase_evaluations(self) -> None:
        self._evaluations += 1

    def increase_generations(self) -> None:
        self._generations += 1

    def increase_no_improvement(self) -> None:
        self._no_improvements += 1

    def reset_generations(self) -> None:
        self._generations = 0
        self._no_improvements = 0

    def serialize(self) -> Dict[str, int]:
        return {
            'generations': self._generations,
            'evaluations': self._evaluations,
            'no_improvements': self._no_improvements,
        }

    @staticmethod
    def Deserialize(obj: Dict) -> Age:
        age = Age()
        age._generations = obj['generations']
        age._evaluations = obj['evaluations']
        age._no_improvements = obj['no_improvements']
        return age
