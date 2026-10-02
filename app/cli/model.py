from pathlib import Path

import typer

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


#  container.run_in_container(command=command, volumes=[])

# # TODO add some tracking e.g.
# mlflow.set_tracking_uri(tracking_uri)
# mlflow.set_experiment(experiment_name)
# with mlflow.start_run() as run:
#     run_id = run.info.run_id

#     data = mlflow.download_artifact(run_id=run_id, artifact_path=data_path)
#     params = mlflow.download_artifact(run_id=run_id, artifact_path=params_path)

#     func(data=data, params=params)
# raise typer.Exit(code)
