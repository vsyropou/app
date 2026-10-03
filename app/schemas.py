"""
Common abstractions shared across packages
"""

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, ConfigDict, Field


def datetime_to_gmt_str(dt: datetime) -> str:
    if not dt.tzinfo:
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))

    return dt.strftime("%Y-%m-%dT%H:%M:%S%z")


class CustomModel(BaseModel):
    model_config = ConfigDict(
        json_encoders={datetime: datetime_to_gmt_str},
        populate_by_name=True,
    )

    def serializable_dict(self, **kwargs: Any) -> Any:
        """Return a dict which contains only serializable fields."""
        default_dict = self.model_dump()

        return jsonable_encoder(default_dict)


class MetadataField(CustomModel):
    field: str
    default_value: Any


class Document(CustomModel):
    source: str = Field(description="The document to index.")
    metadata: dict = Field(default=dict, description="Additional metadata to attach to the indexed data.")


class Features(CustomModel):
    """Typed metadata carried through the pipeline; extra fields are preserved."""

    model_config = ConfigDict(extra="ignore")

    subject: str | None = Field(default=None, description="The subject of the statement.")
    affiliation: str | None = Field(default=None, description="The affiliation of the speaker.")
    speaker_name: str | None = Field(default=None, description="The name of the speaker.")
    subjects: str | None = Field(default=None, description="The subject areas of the statement.")
    speaker_job: str | None = Field(default=None, description="The job of the speaker.")
    speaker_state: str | None = Field(default=None, description="The state of the speaker.")
    speaker_affiliation: str | None = Field(default=None, description="The affiliation of the speaker.")
    statement_context: str | None = Field(default=None, description="The context of the statement.")


class ModelRequest(CustomModel):
    statement: str = Field(description="The statement to be classified.")
    features: Features = Field(description="The data point (features).")
    label: int | None = Field(
        None,
        description="Optional list of labels corresponding to the documents. If provided, evaluation metrics will be returned.",
    )
    meta: dict | None = Field(None, description="Request metadata")


class Score(CustomModel):
    # Verdict fields written by the `llm` transformer.
    is_true: bool | None = Field(default=None, description="Whether the statement is factually true.")
    confidence: float | None = Field(default=None, description="Confidence in the verdict, from 0.0 to 1.0.")
    hint: str | None = Field(default=None, description="One-sentence explanation of the verdict.")


class Metrics(CustomModel):
    accuracy: float = Field(description="The overall accuracy of the evaluation.")
    precision: float = Field(description="The precision of the evaluation.")
    recall: float = Field(description="The recall of the evaluation.")
    f1_score: float = Field(description="The F1 score of the evaluation.")


class ModelResponse(CustomModel):
    scores: list[Score] = Field(description="The actual model responses")
    metrics: Metrics | None = Field(None, description="Optional evaluation metrics if labels were provided.")
    meta: dict | None = Field(None, description="Rsponse metadata")
