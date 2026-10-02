import json
from typing import Any, ClassVar

from pydantic import BaseModel, Field

from app.pipeline.destinations.base import Destination, P


class FileDestination(Destination[Any]):
    """
    Destination for writing items to a file.
    """

    name: ClassVar[str] = "file"
    description: ClassVar[str] = "Append to target file. Uses - for stdout (standard POSIX convention)."

    """Parameters for file destination"""

    filename: str = Field(description="The file to write to.")
    as_json: bool = Field(
        default=False, description="Whether to convert items to JSON before writing them to target file."
    )

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    def _as_json(self, item: P) -> str:
        if isinstance(item, BaseModel):
            return item.model_dump_json()

        return json.dumps(item)

    def ingest(self, item: P) -> None:
        item_str = self._as_json(item) if self.as_json else str(item)
        if self.filename == "-":
            print(item_str)
        else:
            with open(self.filename, "a+", encoding="utf-8") as fp:
                fp.write(item_str)
                fp.write("\n")
