import mlflow
import typer

from app import config as app_config
from app.model import methods
from app.tracking.tracking import init_tracking, log_model, log_params

app = typer.Typer(name="model", help="Model Operations")


@app.command()
def train(
    data: str = typer.Argument(help="Path to the training data. Format is model-specific."),
    params: list[str] = typer.Option([], "--param", "-p", help="Model parameter as key=value. Repeatable."),
) -> None:
    """Train the model and log it to MLflow. Training itself is tracking-free; this command composes the two."""

    cfg = app_config.get_environment_config()
    model_params = dict(p.split("=", 1) for p in params)

    model = methods.PlaceholderModel()
    model.train(data, model_params)

    if cfg.mlflow.enabled:
        init_tracking(cfg.mlflow)
        with mlflow.start_run():
            log_params(model_params)
            log_model(model, artifact_path="model", registered_model_name=cfg.model.name)
    else:
        typer.echo("MLflow tracking disabled, trained model not logged")


@app.command()
def load() -> None:
    """Load the configured model once, verifying config.model.uri is reachable."""

    cfg = app_config.get_environment_config()
    from app.model import dependencies

    dependencies.setup_model(cfg.model)
    typer.echo(f"Model loaded: {dependencies.get_model()}")
