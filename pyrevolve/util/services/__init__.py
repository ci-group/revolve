import platform
from abc import abstractmethod, ABC  # Abstract Base Classes
from typing import AnyStr

import asyncio

from pyrevolve.custom_logging.logger import logger


class ServiceBase(ABC):
    def __init__(self, name: AnyStr):
        self._name: AnyStr = name

    @abstractmethod
    def is_running(self) -> bool:
        raise NotImplementedError("Abstract method")

    @abstractmethod
    async def start(self) -> None:
        raise NotImplementedError("Abstract method")

    def start_sync(self) -> None:
        asyncio.get_event_loop().run_until_complete(self.start())

    @abstractmethod
    async def stop(self) -> None:
        raise NotImplementedError("Abstract method")


if platform.system() == 'Linux':
    from .systemd import SystemdService as Service
else:
    logger.error("Service not supported on your platform, you handle it yourself")
    from .user_managed_service import UserManagedService as Service
