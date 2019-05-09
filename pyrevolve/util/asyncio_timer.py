import asyncio


class AsyncTimer:
    def __init__(self, timeout, callback):
        self._timeout = timeout
        self._callback = callback
        self._task = asyncio.ensure_future(self._job())
        self._stop = False

    async def _job(self):
        await asyncio.sleep(self._timeout)
        await self._callback()
        if not self._stop:
            self._task = asyncio.ensure_future(self._job())

    def cancel(self):
        self._task.cancel()
        self._stop = True
