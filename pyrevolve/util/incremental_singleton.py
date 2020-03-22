
class IncrementalSingleton:

    __instance = None

    #TODO typing instance object
    @staticmethod
    def getInstance():
        """ Static access method. """
        if IncrementalSingleton.__instance == None:
            IncrementalSingleton()
        return IncrementalSingleton.__instance

    _index = 0

    def __init__(self, index=0):
        """ Virtually private constructor. """
        if IncrementalSingleton.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            IncrementalSingleton.__instance = self

        self.initialize(index)

    def initialize(self, index):
        self._index = index

    def index(self):
        return self._index

    def increment(self):
        self._index = self._index + 1
        return self._index

    def reset(self):
        self._index = 0
        return self._index

if __name__ == "__main__":
    gen = IncrementalSingleton(1)
    print(gen.index())
    generation = IncrementalSingleton.getInstance()
    generation.increment()
    print(gen.index(), generation.index())
