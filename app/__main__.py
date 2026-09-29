import warnings

import typer
from pydantic import PydanticDeprecatedSince20
from rich.console import Console

from app import config
from app.cli import db as db_cli
from app.cli import model as model_cli

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=PydanticDeprecatedSince20)
warnings.filterwarnings("ignore", module="pydantic")

app = typer.Typer(
    name="recommender",
    help="ep recommender service cli",
    pretty_exceptions_show_locals=False,
)
app.add_typer(db_cli.app, name="db")
app.add_typer(model_cli.app, name="model")
console = Console()

CONFIG = config.get_environment_config()


@app.command("dummy")
def dummy(
    arg: int = typer.Argument(help="The ID of the user to get recommendations for"),
    opt: int = typer.Option(5, help="Number of recommendations to return"),
) -> None:
    """Get recommendations for a user using the specified algorithm and parameters."""

    console.print("HELLO")
    console.print(f"arg: {arg}, opt: {opt}")
    console.print(CONFIG)
