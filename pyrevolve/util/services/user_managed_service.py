import sys
from typing import AnyStr

from pyrevolve.custom_logging.logger import logger
from pyrevolve.util.services import ServiceBase


class UserManagedService(ServiceBase):
    def __init__(self, name: AnyStr):
        super().__init__(name)
        self._is_running: bool = False

    def is_running(self) -> bool:
        return self._is_running

    async def start(self) -> None:
        logger.warning(f'Ensure the service "{self._name}" is running then press ENTER')
        sys.stdin.readline()  # TODO async
        self._is_running = True

    async def stop(self) -> None:
        logger.warning(f'You can shutdown the service "{self._name}" now')
        self._is_running = False
