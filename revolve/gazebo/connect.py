import trollius
from trollius import From, Return
import pygazebo

# Default connection address to keep things DRY. This is an array
# rather than a tuple, so it is writeable as long as you change
# the separate elements.
default_address = ["127.0.0.1", 11345]

@trollius.coroutine
def connect(address=default_address):
    manager = yield From(pygazebo.connect(address=address))
    raise Return(manager)
