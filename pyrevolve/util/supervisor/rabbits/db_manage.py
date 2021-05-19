import os
import sys
import time
from sys import platform
from typing import AnyStr

import sqlalchemy.orm
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from pyrevolve.util.supervisor.rabbits import db_data
from pyrevolve.custom_logging.logger import logger


def _engine(type: AnyStr, username='username', password='password', address='localhost', dbname='pythoncpptest'):
    # if _engine_type == type and _engine is not None:
    #     return _engine
    if type == 'sqlite':
        _engine = create_engine(f'sqlite:///{dbname}.db')
    elif type == 'postgresql':
        _engine = create_engine(
            # The PostgreSQL dialect uses psycopg2 as the default DBAPI. pg8000 is also available as a pure-Python substitute
            f'postgresql://{username}:{password}@{address}/{dbname}'
        )
    else:
        raise Exception(f'database engine {type} not recognized')
    return _engine


class PostgreSQLDatabase:
    def __init__(self, username='username', password='password', address='localhost', dbname='pythoncpptest'):
        assert(address == 'localhost' or address == '127.0.0.1' or address == '::1')

        self._username = username.strip()
        self._password = password.strip()
        self._address = address.strip()
        self._dbname = dbname.strip()
        self.running = False

        if platform.startswith('linux'):
            # Creates dbus systemd connection
            import dbus
            sysbus = dbus.SystemBus()
            systemd1 = sysbus.get_object('org.freedesktop.systemd1', '/org/freedesktop/systemd1')
            self._systemd_manager = dbus.Interface(systemd1, 'org.freedesktop.systemd1.Manager')

        self.check_running()
        self.start()
        self._engine = create_engine(
            # The PostgreSQL dialect uses psycopg2 as the default DBAPI. pg8000 is also available as a pure-Python substitute
            f'postgresql://{username}:{password}@{address}/{dbname}'
        )
        # Bind the engine to the metadata of the Base class so that the
        # decleratives can be accessed through a DBSession instance
        db_data.Base.metadata.bind = self._engine
        # Generates the sessionmaker, to create sessions
        self._sessionmaker: sessionmaker = sessionmaker(bind=self._engine)

    def check_running(self) -> bool:
        """
        Checks if the database server is running and updates the self.running variable
        :return: True if the server is running
        """
        if platform.startswith('linux'):
            # Ask systemd if the systemd if postgresql is running
            self.running = False
            # https://www.freedesktop.org/wiki/Software/systemd/dbus/
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

                if unit_name == 'postgresql.service':
                    self.running = (unit_active == 'active' and unit_running == 'running')
                    break
            else:
                self.running = False
        else:
            raise NotImplementedError("This function only works on linux at the moment")

        return self.running

    def start(self) -> None:
        """
        Ensures that the database server is running
        """
        if not self.running:
            if platform.startswith('linux'):
                # https://www.freedesktop.org/wiki/Software/systemd/dbus/
                self._systemd_manager.StartUnit('postgresql.service', 'fail')
                while not self.running:
                    logger.info("Postgresql service starting..")
                    time.sleep(1)
                    self.check_running()
                logger.info("Postgresql service running!")
            else:
                print("ensure postgresql server is running then press ENTER")
                sys.stdin.readline()
        self.running = True

    def init_db(self, first_time=False) -> None:
        """
        Database needs to be running before calling this function
        :param first_time: if to also create the user
        """
        if not self.running:
            raise RuntimeError("Cannot init db if database server is not running")

        # CREATE Database user
        if first_time:
            logger.info(f'Creating DB user: {self._username}')
            r = os.system(f'createuser {self._username} --echo --createdb --login --no-createrole --no-superuser --no-replication')
            if r != 0:
                logger.error(f'Error creating Postgres user "{self._username}"')

        # CREATE Database
        logger.info(f'Creating Database: "{self._dbname}" owned by "{self._username}"')
        r = os.system(f'createdb {self._dbname} --echo --owner {self._username}')
        if r != 0:
            logger.error(f'Error creating Database "{self._dbname}"')

        # CREATE Tables
        logger.info(f'Creating tables')
        db_data.create_db(self._engine)

    def session(self) -> sqlalchemy.orm.session:
        """
        A `Session` instance establishes all conversations with the database
        and represents a "staging zone" for all the objects loaded into the
        database session object. Any change made against the objects in the
        session won't be persisted into the database until you call
        `session.commit()`. If you're not happy about the changes, you can
        revert all of them back to the last commit by calling
        `session.rollback()`
        :return: New Database Session
        """
        return self._sessionmaker()

    def disconnect(self) -> None:
        """
        Disconnects from the database.
        Kind of an explicit deconstructor if needed (e.g. before destroying)
        """
        self._sessionmaker = None
        self._engine.dispose()
        self._engine = None

    def destroy(self) -> bool:
        """
        Drops the database, cleaning up disk space.
        Dropping will fail if the engine or some sessions are still connected!
        :return: True if the drop was successful
        """
        logger.info(f'Dropping database "{self._dbname}"')
        r = os.system(f'dropdb {self._dbname} --echo')
        return r == 0
