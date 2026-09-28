import hmac
import pathlib
from logging import getLogger

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.component.methods import get_method
from app.config import AppConfig, get_environment_config
from app.interfaces import IDependency

log = getLogger(__name__)
PWD = pathlib.Path(__file__).parent

_bearer_scheme = HTTPBearer(auto_error=False)


def get_config() -> AppConfig:
    return get_environment_config()


# Placeholder, eg model
def get_component() -> IDependency:
    return get_method()


async def require_bearer(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    cfg: AppConfig = Depends(get_config),
) -> None:
    if cfg.api_token is None:
        return  # auth disabled
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    if not hmac.compare_digest(credentials.credentials.encode(), cfg.api_token.encode()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bearer token")
