from typing import Any

from app.api.schemas import CustomModel


class Response(CustomModel):
    predictions: list[Any]


class Request(CustomModel):
    data: Any
