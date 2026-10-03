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

        # Unify curly quotes/dashes, ellipsis
        normalized_text = normalized_text.translate(
            str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"', "–": "-", "—": "-", "…": "..."})
        )

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


class SplitMetadataTransformer(Transformer):
    """
    Transformer that splits a string metadata field by a delimiter into an ordered list.
    """

    name: ClassVar[str] = "split_metadata"
    description: ClassVar[str] = "Splits a string metadata field by a delimiter into an ordered list"

    field: str = Field(description="The metadata field to split.")
    delimiter: str = Field(default="$", description="The delimiter to split on.")

    def transform(self, document: Document) -> list[Document]:
        """
        Split the configured metadata field into an ordered list.
        """
        metadata = document.metadata.copy()
        value = metadata.get(self.field)
        if isinstance(value, str):
            metadata[self.field] = sorted(s.strip() for s in value.split(self.delimiter) if s.strip())
        return [Document(source=document.source, metadata=metadata)]


class DropNullsTransformer(Transformer):
    """
    Transformer that drops records with null/empty source or null/empty listed metadata fields.
    """

    name: ClassVar[str] = "drop_nulls"
    description: ClassVar[str] = "Drops records with empty source or missing/empty listed metadata fields"

    fields: list[str] = Field(
        default_factory=list,
        description="Metadata fields that must be present and non-empty for the record to survive.",
    )

    def transform(self, document: Document) -> list[Document]:
        """
        Emit [] (drop) when source is empty or any listed field is missing/empty on the metadata.
        """
        if not document.source or not document.source.strip():
            return []
        for field in self.fields:
            value = document.metadata.get(field)
            if value is None:
                return []
            if isinstance(value, str) and not value.strip():
                return []
        return [document]


class DeduplicateTransformer(Transformer):
    """
    Transformer that drops records whose (source, speaker) pair has already been seen.
    Prevents duplicate-statement leakage across splits.
    """

    name: ClassVar[str] = "deduplicate"
    description: ClassVar[str] = "Drops duplicate (source, speaker) pairs to prevent split leakage."

    speaker_field: str = Field(default="speaker_name", description="Metadata field identifying the speaker.")

    def __init__(self, **data) -> None:  # type: ignore[no-untyped-def]
        super().__init__(**data)
        self._seen: set[tuple[str, str]] = set()

    def transform(self, document: Document) -> list[Document]:
        key = (document.source, str(document.metadata.get(self.speaker_field, "")))
        if key in self._seen:
            return []
        self._seen.add(key)
        return [document]


class BucketizeTransformer(Transformer):
    """
    Maps raw values of a metadata field into a small named set of buckets.
    Values not present in the mapping fall into ``other``; empty/missing falls into ``null_bucket``.
    """

    name: ClassVar[str] = "bucketize"
    description: ClassVar[str] = "Maps raw categorical values into a small set of named buckets."

    field: str = Field(description="The metadata field to bucketize.")
    mapping: dict[str, str] = Field(
        description="raw value (case-insensitive) → bucket name. Anything not mapping lands in ``other``."
    )
    other: str = Field(default="other", description="Bucket for values not present in mapping.")
    null_bucket: str = Field(default="none", description="Bucket for missing/empty values.")

    def transform(self, document: Document) -> list[Document]:
        metadata = document.metadata.copy()
        value = metadata.get(self.field)
        if not isinstance(value, str) or not value.strip():
            metadata[self.field] = self.null_bucket
        else:
            metadata[self.field] = self.mapping.get(value.strip().lower(), self.other)
        return [Document(source=document.source, metadata=metadata)]


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
