from pathlib import Path

import typer

from app import container
from app.config import get_environment_config

app = typer.Typer(name="model", help="Model Operations")


@app.command()
def load() -> None:
    """Load the configured model once, verifying config.model.uri is reachable."""

    cfg = get_environment_config()
    from app.model import dependencies

    dependencies.setup_model(cfg.model)
    typer.echo(f"Model loaded: {dependencies.get_model()}")


@app.command()
def train(
    data: Path = typer.Option(..., "--data", help="data path."),
    conf: Path = typer.Option(..., "--conf", help="configuration."),
) -> None:
    """Run a command in an ephemeral container built from app/model + deps.toml."""

    cnf = get_environment_config()
    uri = cnf.mlflow.tracking_uri
    name = cnf.mlflow.experiment_name

    command = [
        f"uv run python runner.py train --module model --data {data} --conf {conf} --tracking-uri {uri} --experiment-name {name}"
    ]

    container.run_in_container(command=command, volumes=[])
    raise typer.Exit(code)
