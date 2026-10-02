"""
Text cleaning transformers for the pipeline.
"""

import re
import unicodedata
from typing import ClassVar, Literal

from jinja2 import Environment, Template, TemplateSyntaxError
from pydantic import Field, field_validator
from spacy.lang.en.stop_words import STOP_WORDS

from app.pipeline.transformers.base import Transformer
from app.schemas import Document, MetadataField


class LowercaseTransformer(Transformer):  # Non-generic since no params
    """
    Transformer that converts text to lowercase.
    """

    name: ClassVar[str] = "lowercase"
    description: ClassVar[str] = "Converts all text to lowercase"

    def transform(self, document: Document) -> list[Document]:
        """
        Convert the document's text to lowercase.

        :param document: The document to transform.
        :return: A list containing the transformed document.
        """
        return [Document(source=document.source.lower(), metadata=document.metadata.copy())]


class RemoveStopwordsTransformer(Transformer):
    """
    Transformer that removes stopwords from text.
    """

    name: ClassVar[str] = "remove_stopwords"
    description: ClassVar[str] = "Removes common stopwords from the text"
    stopwords: set[str] = Field(
        default=STOP_WORDS,
        description="Custom set of stopwords to remove. If not provided, default English stopwords will be used.",
    )

    def transform(self, document: Document) -> list[Document]:
        """
        Remove stopwords from the document's text.

        :param document: The document to transform.
        :return: The input document without the stopwords.
        """
        words = document.source.split()
        filtered_words = [word for word in words if word.lower() not in self.stopwords]
        filtered_text = " ".join(filtered_words)

        return [Document(source=filtered_text, metadata=document.metadata.copy())]


class RemoveUnicodeTransformer(Transformer):
    """
    Transformer that removes or normalizes Unicode characters.
    """

    name: ClassVar[str] = "remove_unicode"
    description: ClassVar[str] = "Normalizes or removes Unicode characters from text"

    mode: Literal["normalize", "remove"] = Field(
        default="normalize",
        description="Mode for handling Unicode: 'normalize' converts to ASCII equivalents, 'remove' discards non-ASCII",
    )

    def transform(self, document: Document) -> list[Document]:
        """
        Process Unicode characters in the document's text.

        :param document: The document to transform.
        :return: A list containing the transformed document.
        """
        if self.mode == "normalize":
            # Normalize to NFKD form and then keep only ASCII chars
            normalized_text = unicodedata.normalize("NFKD", document.source)
            # This keeps the ASCII equivalent of accented characters
            normalized_text = "".join(c for c in normalized_text if not unicodedata.combining(c))

            return [Document(source=normalized_text, metadata=document.metadata.copy())]
        else:  # remove mode
            # Remove all non-ASCII characters
            ascii_text = re.sub(r"[^\x00-\x7F]+", "", document.source)

            return [Document(source=ascii_text, metadata=document.metadata.copy())]


class TextNormalizationTransformer(Transformer):
    """
    Transformer that normalizes text by removing extra whitespace, standardizing punctuation, etc.
    """

    name: ClassVar[str] = "text_normalization"
    description: ClassVar[str] = "Normalizes text by removing extra whitespace and standardizing punctuation"

    def transform(self, document: Document) -> list[Document]:
        """
        Normalize the document's text.

        :param document: The document to transform.
        :return: A list containing the transformed document.
        """
        # Replace multiple spaces with a single space
        normalized_text = re.sub(r"\s+", " ", document.source)

        # Standardize punctuation (e.g., multiple periods to a single one)
        normalized_text = re.sub(r"\.{2,}", ".", normalized_text)
        normalized_text = re.sub(r"\!{2,}", "!", normalized_text)
        normalized_text = re.sub(r"\?{2,}", "?", normalized_text)

        # Trim whitespace
        normalized_text = normalized_text.strip()

        return [Document(source=normalized_text, metadata=document.metadata.copy())]


class TemplateSourceTransformer(Transformer):
    """
    Transformer that applies a jinja template to the document's source.
    """

    name: ClassVar[str] = "template"
    description: ClassVar[str] = "Applies a template to the document's source"

    template: str = Field(description="The jinja template to apply to the document's source")

    @field_validator("template", mode="before")
    @classmethod
    def validate_template_syntax(cls, v: str) -> str:
        """Validate that the template string has valid Jinja2 syntax."""
        if not isinstance(v, str):
            raise ValueError(f"Template must be a string, got {type(v).__name__}")

        try:
            env = Environment()
            env.parse(v)
            return v
        except TemplateSyntaxError as e:
            raise ValueError(f"Invalid Jinja2 template syntax: {e}")
        except Exception as e:
            raise ValueError(f"Template validation failed: {e}")

    def transform(self, document: Document) -> list[Document]:
        """
        Apply a jinja template to the document's source.
        """
        template_obj = Template(self.template)
        return [Document(source=template_obj.render(document), metadata=document.metadata.copy())]


class FilterMetadataTransformer(Transformer):
    """
    Transformer that filters the document's metadata.
    """

    name: ClassVar[str] = "filter-metadata"
    description: ClassVar[str] = "Filters the document's metadata"

    metadata: list[MetadataField] = Field(
        description="The metadata to keep. Schema of each list element: {field:<name>, default_value:<value>}"
    )

    def transform(self, document: Document) -> list[Document]:
        """
        Filter the document's metadata.
        """

        metadata = {}
        for m in self.metadata:
            value = document.metadata.get(m.field, m.default_value)
            if isinstance(value, str) and not value.strip():
                value = m.default_value
            metadata[m.field] = value

        return [Document(source=document.source, metadata=metadata)]
