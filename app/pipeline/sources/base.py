from abc import ABC
from collections.abc import Iterable
from typing import ClassVar

from pydantic import BaseModel

from app.types import DataItem


class Source(ABC, BaseModel, Iterable[DataItem]):
    """
    Source interface.

    A source has some configuration and emits documents.
    """

    # Class variables to be defined by subclasses
    name: ClassVar[str]  # User-friendly name for the source
    description: ClassVar[str] = ""  # Optional description

    class Config:
        extra = "forbid"
