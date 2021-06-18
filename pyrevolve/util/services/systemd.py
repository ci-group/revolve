import platform

import asyncio
import dbus
from typing import AnyStr

from dbus import DBusException

from pyrevolve.custom_logging.logger import logger
from pyrevolve.util.services import ServiceBase

if platform.system() != 'Linux':
    logger.error("Should not import this file if you are not on Linux, will probably crash")


class SystemdService(ServiceBase):
    def __init__(self, name: AnyStr):
        super().__init__(name)
        self._service_name = f'{name.lower()}.service'
        self._is_running: bool = False
        self._system_bus = dbus.SystemBus()
        self._systemd1 = self._system_bus.get_object('org.freedesktop.systemd1', '/org/freedesktop/systemd1')
        self._systemd_manager = dbus.Interface(self._systemd1, 'org.freedesktop.systemd1.Manager')

    def is_running(self):
        """
        Checks if the service is running
        """
        self._check_is_running()
        return self._is_running

    async def start(self):
        """
        Starts the service
        :raises DBusException:
        """
        self._check_is_running()
        if not self._is_running:
            # https://www.freedesktop.org/wiki/Software/systemd/dbus/
            self._systemd_manager.StartUnit(self._service_name, 'fail')
            while not self._is_running:
                logger.info(f"{self._name} service starting..")
                await asyncio.sleep(1)
                self._check_is_running()
            logger.info(f"{self._name} service running!")
        else:
            logger.warning("Service was already running")

    async def stop(self):
        """
        Stops the service
        :raises DBusException:
        """
        self._check_is_running()
        if self._is_running:
            # https://www.freedesktop.org/wiki/Software/systemd/dbus/
            try:
                r = self._systemd_manager.StopUnit(self._service_name, 'fail')
            except DBusException as e:
                if e.get_dbus_name() == 'org.freedesktop.DBus.Error.AccessDenied'\
                        and e.get_dbus_message() == 'Permission denied':
                    logger.warning("Could not stop service, permission denied")
                else:
                    raise
            while self._is_running:
                # TODO if authentication failed, should not try forever to stop the service
                logger.info(f"{self._name} service stopping..")
                await asyncio.sleep(1)
                self._check_is_running()
            logger.info(f"{self._name} service stopped!")
        else:
            logger.warning("Service was already stopped")

    def _check_is_running(self):
        """
        Checks with systemd if the database is running
        :return: True if it's running
        """
        self._is_running = False
        systemd_units = self._systemd_manager.ListUnits()
        for unit in systemd_units:
            # The `unit` variable returned from dbus.ListUnits() has the following properties:
            # - The primary unit name as string
            unit_name: AnyStr = unit[0]
            # - The human readable description string
            unit_desc: AnyStr = unit[1]
            # - The load state (i.e. whether the unit file has been loaded successfully)
            unit_loaded: AnyStr = unit[2]
            # - The active state (i.e. whether the unit is currently started or not)
            unit_active: AnyStr = unit[3]
            # - The sub state (a more fine-grained version of the active state that is specific to the unit type, which the active state is not)
            unit_running: AnyStr = unit[4]
            # - A unit that is being followed in its state by this unit, if there is any, otherwise the empty string.
            # - The unit object path
            # - If there is a job queued for the job unit the numeric job id, 0 otherwise
            # - The job type as string
            # - The job object path

            if unit_name == self._service_name:
                self.running = (unit_active == 'active' and unit_running == 'running')
                self._is_running = True
                break
        else:
            self._is_running = False

        return self._is_running
