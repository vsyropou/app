import pathlib
from logging import getLogger

from app.component.methods import get_method
from app.config import AppConfig, get_environment_config

log = getLogger(__name__)
PWD = pathlib.Path(__file__).parent


def get_config() -> AppConfig:
    return get_environment_config()


# Placeholder, eg model
def get_component():  # -> IDependency:
    return get_method()
