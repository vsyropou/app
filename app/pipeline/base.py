"""
Base pipeline for text processing.
"""

from collections.abc import Iterable
from uuid import uuid4

from app.pipeline.transformers.base import Transformer
from app.schemas import Document


class Pipeline:
    """
    A pipeline for processing text documents through a series of transformers.

    A pipeline consists of a sequence of transformers that are applied in order.
    Documents flow through the pipeline, with each transformer potentially modifying
    the documents before passing them to the next transformer.
    """

    def __init__(self, transformers: list[tuple[str, Transformer] | Transformer]) -> None:
        """
        Initialize a pipeline with a list of transformers.

        :param transformers: A list of transformers, each optionally with a name. If a transformer doesn't have a name,
                       one will be generated.
        """
        self.transformers: list[tuple[str, Transformer]] = [
            (str(uuid4()), item) if isinstance(item, Transformer) else item for item in transformers
        ]

    def __len__(self) -> int:
        """
        Get the number of transformers in the pipeline.

        :return: The number of transformers.
        """
        return len(self.transformers)

    def process(self, documents: Iterable[Document]) -> list[Document]:
        """
        Process documents through all transformers in the pipeline.

        :param documents: The documents to process.
        :return: The processed documents.
        """

        current_documents = list(documents)

        for _, transformer in self.transformers:
            new_documents = []
            for doc in current_documents:
                new_documents.extend(transformer(doc))
            current_documents = new_documents

        return current_documents

    def __call__(self, documents: Iterable[Document]) -> list[Document]:
        """
        Call the pipeline with documents.

        :param documents: The documents to process.
        :return: The processed documents.
        """
        return self.process(documents)
