import csv
from pathlib import Path
from typing import ClassVar

from pydantic import Field, FilePath

from app.pipeline.sources.base import Source
from app.types import DataItem


class CSVSource(Source):
    """
    Source for reading rows from a CSV file.

    Yields each row as a dict keyed by header column names.
    """

    name: ClassVar[str] = "csv"
    description: ClassVar[str] = "Source for reading rows from a CSV file"

    file_path: FilePath = Field(description="Path to the CSV file to read")
    encoding: str = Field(default="utf-8", description="File encoding to use when reading")

    def __iter__(self) -> DataItem:
        with Path(self.file_path).open(encoding=self.encoding) as fp:
            yield from csv.DictReader(fp)
