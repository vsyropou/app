import json
import os
from pathlib import Path
from typing import ClassVar

from pydantic import Field, FilePath

from app.pipeline.sources.base import Source
from app.types import DataItem


class JSONLSource(Source):
    """
    Source for reading data from a JSON Lines file.

    Each line in the file should be a valid JSON object.
    """

    name: ClassVar[str] = "jsonl"
    description: ClassVar[str] = "Source for reading data from a JSON Lines file"

    """Parameters for a JSONL source."""

    file_path: FilePath = Field(description="Path to the JSONL file to read")
    encoding: str = Field(default="utf-8", description="File encoding to use when reading")
    offset: int = Field(default=0, description="Number of lines to skip from the beginning of the file")
    limit: int | None = Field(default=None, description="Optional maximum number of lines to read")
    raise_on_error: bool = Field(default=True, description="Whether to raise an error on invalid JSON")

    def __iter__(self) -> DataItem:
        """
        Reads a JSONL file line by line.

        :return: Each line as a DataItem
        """
        file_path = Path(self.file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"JSONL file not found: {self.file_path}")

        if os.path.getsize(file_path) == 0:
            raise RuntimeError(f"JSONL file is empty: {self.file_path}")

        lines_read = 0
        lines_processed = 0

        with open(file_path, "r", encoding=self.encoding) as file:  # noqa: UP015
            for line in file:
                lines_read += 1

                # Skip empty stuff
                if line.isspace() or not line:
                    continue

                # Skip lines until we reach the offset
                if lines_read <= self.offset:
                    continue

                # Check if we've hit the limit
                if self.limit is not None and lines_processed >= self.limit:
                    break

                try:
                    # Deserialize the JSON line
                    data = json.loads(line)

                    lines_processed += 1
                    yield data
                except json.JSONDecodeError as e:
                    if self.raise_on_error:
                        raise ValueError(f"Invalid JSON at line {lines_read}: {line}") from e
