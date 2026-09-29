from logging import getLogger

from app.config import ModelConfig
from app.model.interfaces import IModel
from app.model.methods import get_method

logger = getLogger(__name__)

# Holds the serving model. Loaded once (from MLflow URI or local path), avoids reloading per request.
_model: IModel | None = None


def setup_model(config: ModelConfig) -> None:
    """Load the serving model from config.model.uri. Falls back to the placeholder when unset."""
    global _model
    if _model is not None:
        return
    if not config.uri:
        logger.info("No model URI configured, using placeholder model")
        _model = get_method()
        return
    from mlflow.pyfunc import load_model

    logger.info("Loading model %s", config.uri)
    _model = load_model(config.uri)  # type: ignore[assignment]
    logger.info("Done loading model")


def get_model() -> IModel:
    return _model or get_method()
