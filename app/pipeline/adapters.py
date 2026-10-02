"""
Adapter components to convert between different data types in the pipeline.
"""

from abc import ABC, abstractmethod
from textwrap import dedent
from typing import ClassVar

from pydantic import BaseModel, Field

from app.schemas import Document
from app.types import DataItem


class Adapter(ABC, BaseModel):
    """
    Base adapter interface for converting between different data types.
    """

    name: ClassVar[str]  # User-friendly name for the source
    description: ClassVar[str] = ""  # Optional description

    @abstractmethod
    def adapt(self, item: DataItem) -> Document:
        """
        Convert an item from one type to another.

        :param item: The input item to convert
        :return: The converted item
        """
        pass


class NoopAdapter(Adapter):
    """
    Adapter that converts the data item to the source of the document.
    """

    name: ClassVar[str] = "noop"
    description: ClassVar[str] = "Converts the input to a document without metadata"

    def adapt(self, item: DataItem) -> Document:
        return Document(source=str(item))


class FieldExtractorDocumentAdapter(Adapter):
    """
    Adapter that keeps a specific field from a dictionary.
    """

    name: ClassVar[str] = "field"
    description: ClassVar[str] = """
    Extracts the specific field from a dict, while keeping the rest of the dict as the metadata.
    Useful for converting JSON documents to instances of Document.
    """
    field: str = Field(description="The field to use for extracting the text")
    default_value: str | None = Field(
        None,
        description=dedent("""
        The value to use if the field value is null, empty string or whitespace-only.
        If it is not specified, the adapter will fail when the one of the cases is encountered.
        """),
    )

    def adapt(self, item: DataItem) -> Document:
        # If it's a dict with the right keys, convert it
        if not isinstance(item, dict):
            raise ValueError("Input is not a dict")

        if self.field not in item:
            raise ValueError(f"Required field '{self.field}' is missing from input")

        value = item[self.field]
        if value is None:
            if self.default_value is None:
                raise ValueError(f"Field '{self.field}' has null value and no default is specified")
            value = self.default_value
        if not value.strip():
            if self.default_value is None:
                raise ValueError(f"Field '{self.field}' is empty or only whitespace and no default is specified")
            value = self.default_value

        return Document(source=value, metadata=item)
