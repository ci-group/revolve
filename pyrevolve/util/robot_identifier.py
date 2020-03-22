from pyrevolve.util.incremental_singleton import IncrementalSingleton


class RobotIdentifier(IncrementalSingleton):

    def __init__(self, index=0):
        super().__init__(index)


if __name__ == "__main__":
    gen = RobotIdentifier(1)
    print(gen.index())
    generation = RobotIdentifier.getInstance()
    generation.increment()
    print(gen.index(), generation.index())
