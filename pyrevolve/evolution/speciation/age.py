
class Age:

    def __init__(self):
        # Age of the species (in generations)
        self._generations: int = 0
        # Age of the species (in evaluations)
        self._evaluations: int = 0

        # generational counter.
        self._no_improvements: int = 0

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
