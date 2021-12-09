import os
from typing import AnyStr, Optional

import sqlalchemy.orm
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from pyrevolve.util.services import Service, UserManagedService
from pyrevolve.util.supervisor.rabbits import db_data
from pyrevolve.custom_logging.logger import logger


def _engine(type: AnyStr, username='username', password='password', address='localhost', dbname='pythoncpptest') -> Engine:
    # if _engine_type == type and _engine is not None:
    #     return _engine
    if type == 'sqlite':
        _engine: Engine = create_engine(f'sqlite:///{dbname}.db')
    elif type == 'postgresql':
        _engine: Engine = create_engine(
            # The PostgreSQL dialect uses psycopg2 as the default DBAPI. pg8000 is also available as a pure-Python substitute
            f'postgresql://{username}:{password}@{address}/{dbname}'
        )
    else:
        raise Exception(f'database engine {type} not recognized')
    return _engine


class PostgreSQLDatabase:
    def __init__(self, username='revolve', password='revolve', address='localhost', dbname='revolve'):
        assert(address == 'localhost' or address == '127.0.0.1' or address == '::1')

        self._username = username.strip()
        self._password = password.strip()
        self._address = address.strip()
        self._dbname = dbname.strip()

        if address == 'localhost':
            self.postgres_service: Service = Service('PostgreSQL')
        else:
            self.postgres_service: Service = UserManagedService('PostgreSQL')

        self._engine: Optional[Engine] = None
        self._sessionmaker: sessionmaker = None

    def check_running(self) -> bool:
        """
        Checks if the database server is running and updates the self.running variable
        :return: True if the server is running
        """
        return self.postgres_service.is_running()

    async def start(self) -> None:
        """
        Ensures that the database server is running
        """
        await self.postgres_service.start()

        self._engine: Engine = create_engine(
            # The PostgreSQL dialect uses psycopg2 as the default DBAPI. pg8000 is also available as a pure-Python substitute
            f'postgresql://{self._username}:{self._password}@{self._address}/{self._dbname}'
        )
        # Bind the engine to the metadata of the Base class so that the
        # decleratives can be accessed through a DBSession instance
        db_data.Base.metadata.bind = self._engine
        # Generates the sessionmaker, to create sessions
        self._sessionmaker: sessionmaker = sessionmaker(bind=self._engine)

    def start_sync(self) -> None:
        """
        SYNC VERSION Ensures that the database server is running
        """
        self.postgres_service.start_sync()

        self._engine: Engine = create_engine(
            # The PostgreSQL dialect uses psycopg2 as the default DBAPI. pg8000 is also available as a pure-Python substitute
            f'postgresql://{self._username}:{self._password}@{self._address}/{self._dbname}'
        )
        # Bind the engine to the metadata of the Base class so that the
        # decleratives can be accessed through a DBSession instance
        db_data.Base.metadata.bind = self._engine
        # Generates the sessionmaker, to create sessions
        self._sessionmaker: sessionmaker = sessionmaker(bind=self._engine)

    def init_db(self, first_time=False) -> None:
        """
        Database needs to be running before calling this function
        :param first_time: if to also create the user
        """
        if not self.postgres_service.is_running():
            raise RuntimeError("Cannot init db if database server is not running")

        # CREATE Database user
        if first_time:
            logger.info(f'Creating DB user: {self._username}')
            r = os.system(f'createuser {self._username} --echo --createdb --login --no-createrole --no-superuser --no-replication --no-password')
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

    def session(self) -> sqlalchemy.orm.Session:
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
        if self._engine is not None:
            self._engine.dispose()
            self._engine: Optional[Engine] = None

    def destroy(self) -> bool:
        """
        Drops the database, cleaning up disk space.
        Dropping will fail if the engine or some sessions are still connected!
        :return: True if the drop was successful
        """
        logger.info(f'Dropping database "{self._dbname}"')
        r = os.system(f'dropdb {self._dbname} --echo')
        return r == 0
