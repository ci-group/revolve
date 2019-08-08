class StreamEnded(Exception):
    pass


class PrettyStreamReader(object):
    def __init__(self, stream):
        self._stream = stream

    async def readline(self):
        if self._stream.at_eof():
            raise StreamEnded()
        line = await self._stream.readline()
        return line.decode('utf-8').strip()

    def at_eof(self):
        return self._stream.at_eof()
