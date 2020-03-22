from pyrevolve.util.incremental_singleton import IncrementalSingleton


class Generation(IncrementalSingleton):

    def __init__(self, number_of_generations=0):
        super().__init__()
        self.number_of_generations = number_of_generations

    def increment(self):
        if not self.done:
            return super().increment()

    def done(self):
        return self._index < self.number_of_generations - 1

if __name__ == "__main__":
    g = Generation(1)
    print(g.index())
    generation: Generation = Generation.getInstance()
    generation.increment()
    print(g.index(), generation.index())
