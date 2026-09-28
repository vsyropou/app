"""
Database configuration and conventions
"""

from logging import getLogger

from sqlalchemy import Engine, MetaData, create_engine

from app.config import DatabaseConfig

logger = getLogger(__name__)

POSTGRES_INDEXES_NAMING_CONVENTION = {
    "ix": "%(column_0_label)s_idx",
    "uq": "%(table_name)s_%(column_0_name)s_key",
    "ck": "%(table_name)s_%(constraint_name)s_check",
    "fk": "%(table_name)s_%(column_0_name)s_fkey",
    "pk": "%(table_name)s_pkey",
}


class Database:
    def __init__(self, metadata: MetaData) -> None:
        self.engine: Engine
        self._metadata = metadata

    def init(self, config: DatabaseConfig) -> None:
        """
        Configure database object.

        :param config: read configuration parameters from this dictionary
        """
        logger.info("Initializing database connection")
        self.configure_schema(config.schema_name)

        args = {}
        if config.ssl_mode:
            args["sslmode"] = config.ssl_mode

        self.engine = create_engine(
            config.connection_url(),
            pool_pre_ping=config.pool_pre_ping,
            pool_size=config.pool_size,
            pool_recycle=config.pool_recycle,
            connect_args=args,
        )

    def configure_schema(self, schema: str) -> None:
        """
        Helper function to configure the schema of tables metadata.

        :param str schema: The name of the schema to use
        """
        self._metadata.schema = schema

        # Schema definition is set per table/index statically
        # So you must update each table in the metadata context
        for t in self._metadata.tables.values():
            t.schema = schema

        for seq in self._metadata._sequences.values():
            seq.schema = schema


metadata = MetaData(naming_convention=POSTGRES_INDEXES_NAMING_CONVENTION)
database = Database(metadata)
