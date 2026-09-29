from typing import Any

from pydantic import Field

from app.api.schemas import CustomModel


class PredictRequest(CustomModel):
    """Generic prediction request, agnostic to the underlying model stack."""

    inputs: list[Any] = Field(
        title="Inputs", description="Input records to predict on. Schema is model-specific.", default_factory=list
    )
    top_n: int = Field(title="Top-N", description="Number of predictions to return per input.", default=5, ge=1, le=100)


class PredictionItem(CustomModel):
    """A single prediction result."""

    output: Any = Field(title="Output", description="The predicted output. Type is model-specific.")
    score: float | None = Field(title="Score", description="Optional score used to rank predictions.", default=None)
    meta: dict[str, Any] = Field(
        title="Metadata", description="Metadata from the underlying model. Useful for debugging.", default_factory=dict
    )


class PredictionResponse(CustomModel):
    """Generic prediction response."""

    predictions: list[PredictionItem] = Field(
        title="Predictions", description="List of predictions, model-defined order."
    )
