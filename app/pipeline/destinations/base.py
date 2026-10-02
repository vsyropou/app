from abc import ABC, abstractmethod
from typing import ClassVar, TypeVar

from pydantic import BaseModel

P = TypeVar("P")


class Destination[P](ABC, BaseModel):
    """
    Definition of a destination.
    """

    # Class variables to be defined by subclasses
    name: ClassVar[str]  # User-friendly name for the destination
    description: ClassVar[str] = ""  # Optional description

    @abstractmethod
    def ingest(self, item: P) -> None:
        """
        Ingest provided item.

        :param item: The item to ingest.
        """
        pass
