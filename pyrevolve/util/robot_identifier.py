

class RobotIdentifier:

    __instance = None

    @staticmethod
    def getInstance():
        """ Static access method. """
        if RobotIdentifier.__instance == None:
            RobotIdentifier()
        return RobotIdentifier.__instance

    _index = 1
    _is_initialized = False

    def __init__(self, index=0):
        """ Virtually private constructor. """
        if RobotIdentifier.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            RobotIdentifier.__instance = self

        self._index = index

    # TODO remove initialize
    def initialize(self, index):
        if self._is_initialized:
            raise Exception("Already initialized robot identifier.")
        else:
            self._index = index

    def next(self):
        self._increment()
        return self.index()

    def index(self):
        return self._index

    def _increment(self):
        self._index = self._index + 1


if __name__ == "__main__":
    gen = RobotIdentifier(1)
    print(gen.index)
    generation = RobotIdentifier.getInstance()
    generation.increment()
    print(gen.index, generation.index)
