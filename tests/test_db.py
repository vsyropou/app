from sqlalchemy import Column, Integer, MetaData, Table

import app.db
from app.config import get_environment_config
from app.db import Database


class TestDatabase:
    def test_connection_url_built_correctly(self) -> None:
        ## GIVEN: a test-environment config
        config = get_environment_config("test")

        ## WHEN: connection_url is called
        url = config.database.connection_url()

        ## THEN: the URL matches the expected default
        assert url == "postgresql+psycopg://app:password@localhost:5432/app"

    def test_configure_schema_retargets_metadata_and_tables(self) -> None:
        ## GIVEN: a fresh MetaData with one dummy table
        metadata = MetaData()
        Table("example", metadata, Column("id", Integer, primary_key=True))
        database = Database(metadata)

        ## WHEN: configure_schema is called
        database.configure_schema("other")

        ## THEN: the metadata and the table are re-targeted
        assert metadata.schema == "other"
        assert metadata.tables["example"].schema == "other"

    def test_example_table_registered_on_shared_metadata(self) -> None:
        ## THEN: importing app.models registers the example table on app.db.metadata
        assert "example" in app.db.metadata.tables
        table = app.db.metadata.tables["example"]
        assert set(table.columns.keys()) == {"id", "name"}
