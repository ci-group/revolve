
class FakeSession:
    def add(self, _):
        return

    def commit(self):
        return


class FakeSessionThing:
    def __enter__(self):
        return FakeSession()

    def __exit__(self, exc_type, exc_val, exc_tb):
        return


class FakeDB:
    def session(self):
        return FakeSessionThing()


def create_fakedb():
    return FakeDB()
