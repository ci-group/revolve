"""
Non-blocking stream reader to read data from a subprocess
without the supervisor stalling. Code taken from:

http://eyalarubas.com/python-subproc-nonblock.html
"""
from threading import Thread
from Queue import Queue, Empty


class NonBlockingStreamReader:
    def __init__(self, stream):
        """
        stream: the stream to read from.
                Usually a process' stdout or stderr.
        """

        self._s = stream
        self._q = Queue()

        def _populate_queue(stream, queue):
            """
            Collect lines from 'stream' and put them in 'queue'.
            """

            while True:
                line = stream.readline()
                if line:
                    queue.put(line)
                else:
                    # This used to throw an exception, but we cannot
                    # catch it, and in any case don't need it right now.
                    break

        self._t = Thread(target=_populate_queue,
                         args=(self._s, self._q))
        self._t.daemon = True

        # start collecting lines from the stream
        self._t.start()

    def readline(self, timeout=None):
        try:
            return self._q.get(block=timeout is not None,
                               timeout=timeout)
        except Empty:
            return None
