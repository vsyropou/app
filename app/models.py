from sqlalchemy import Column, Integer, String, Table

from app.db import metadata

example = Table(
    "example",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(255), nullable=False),
)
