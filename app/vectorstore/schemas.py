from typing import Any

from pydantic import BaseModel


class Document(BaseModel):
    id: str
    text: str
    metadata: dict[str, Any] = {}
    embedding: list[float]


class SearchResult(BaseModel):
    id: str
    text: str
    metadata: dict[str, Any] = {}
    score: float
