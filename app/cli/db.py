import pathlib

import typer
from alembic.command import downgrade as downgrade_db
from alembic.command import upgrade as upgrade_db
from alembic.config import Config
from rich.console import Console
from sqlalchemy.exc import DatabaseError

from app import config as app_config
from app.db import database

PWD = pathlib.Path(__file__).parent

console = Console()
error_console = Console(stderr=True, style="bold red")

app = typer.Typer(name="db", help="Database Operations")


def _get_alembic_config() -> Config:
    """Create and configure Alembic config with database connection details."""
    cfg = app_config.get_environment_config()
    alembic_cfg = Config(str(PWD / ".." / "conf" / "alembic.ini"))
    alembic_cfg.set_main_option("sqlalchemy.url", cfg.database.connection_url())
    database.configure_schema(cfg.database.schema_name)
    return alembic_cfg


def _print_connection_details() -> None:
    cfg = app_config.get_environment_config().database
    error_console.print(
        f"Postgres connection: {cfg.scheme}://{cfg.username}:****@{cfg.host}:{cfg.port}/{cfg.database}?sslmode={cfg.ssl_mode}"
    )
    error_console.print(f"Schema: {cfg.schema_name}")


@app.command()
def initdb() -> None:
    """
    Initialize database.
    """
    upgrade(to_revision="head")


@app.command()
def upgrade(to_revision: str = typer.Argument("head", help="The Alembic revision to upgrade to.")) -> None:
    """
    Upgrade database to specific revision.
    """
    try:
        alembic_cfg = _get_alembic_config()
        upgrade_db(alembic_cfg, to_revision)
    except DatabaseError as e:
        error_console.print(f"Error running migrations: {e!s}")
        _print_connection_details()
        raise typer.Exit(1)


@app.command()
def downgrade(to_revision: str = typer.Argument("base", help="The Alembic revision to downgrade to.")) -> None:
    """
    Downgrade database to specific revision.
    """
    try:
        alembic_cfg = _get_alembic_config()
        downgrade_db(alembic_cfg, to_revision)
    except DatabaseError as e:
        error_console.print(f"Error running migrations: {e!s}")
        _print_connection_details()
        raise typer.Exit(1)
