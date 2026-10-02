"""
Base transformer interface for pipeline components.
"""

from abc import ABC, abstractmethod
from typing import ClassVar

from pydantic import BaseModel

from app.schemas import Document


class Transformer(ABC, BaseModel):
    """
    Base transformer interface for pipeline components.

    A transformer takes a document and returns a list of documents
    after applying some transformation.
    """

    # Class variables to be defined by subclasses
    name: ClassVar[str]  # User-friendly name for the transformer
    description: ClassVar[str] = ""  # Optional description

    @abstractmethod
    def transform(self, document: Document) -> list[Document]:
        """
        Transform the given document into a list of documents.

        Args:
            document: The document to transform.

        Returns:
            A list of transformed documents.
        """
        pass

    def __call__(self, document: Document) -> list[Document]:
        """
        Call the transformer with a document.

        Args:
            document: The document to transform.

        Returns:
            A list of transformed documents.
        """
        return self.transform(document)

    @classmethod
    def get_full_class_path(cls) -> str:
        """
        Get the fully qualified class path.

        Returns:
            The fully qualified class path as a string.
        """
        return f"{cls.__module__}.{cls.__name__}"
