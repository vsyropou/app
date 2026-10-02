import warnings

import typer
from pydantic import PydanticDeprecatedSince20

from app.cli import model as model_cli
from app.cli import ollama as ollama_cli
from app.cli import pipeline as pipeline_cli

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=PydanticDeprecatedSince20)
warnings.filterwarnings("ignore", module="pydantic")

app = typer.Typer(
    name="recommender",
    help="ep recommender service cli",
    pretty_exceptions_show_locals=False,
)
app.add_typer(model_cli.app, name="model")
app.add_typer(ollama_cli.app, name="ollama")
app.add_typer(pipeline_cli.app, name="pipeline")
