from pathlib import Path

from transformers import Pipeline

from app.schemas import Document, Metrics, ModelRequest, ModelResponse, Score

PWD = Path(__file__).parent


def _evaluate(verdicts: list[bool], labels: list[int]) -> Metrics:
    """Score verdicts against labels (1 = true, 0 = false)."""
    tp = sum(1 for v, l in zip(verdicts, labels) if v and l == 1)
    fp = sum(1 for v, l in zip(verdicts, labels) if v and l == 0)
    fn = sum(1 for v, l in zip(verdicts, labels) if not v and l == 1)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    accuracy = sum(1 for v, l in zip(verdicts, labels) if v == (l == 1)) / len(labels)
    return Metrics(accuracy=accuracy, precision=precision, recall=recall, f1_score=f1)


def score(requests: list[ModelRequest], pipeline: Pipeline) -> list[Score]:
    # TODO: enable batching / pagination as a parameter

    docs = [Document(source=req.statement, metadata=req.features.model_dump()) for req in requests]

    rsps = pipeline.process(docs)

    return [Score(**s.metadata) for s in rsps]


def predict(requests: list[ModelRequest], pipeline: Pipeline) -> ModelResponse:
    """Compose the predict function"""

    scores = score(requests=requests, pipeline=pipeline)

    # Optional: evaluation
    labels = [r.label for r in requests if r.label]

    metrics = None
    meta = None
    if len(labels) == 0:
        pass
    # TODO: More safety for when the model does not response correctly
    elif len(labels) != len(requests):
        meta["error"] = "Not every data point has a true label. Skipping evaluation."
    else:
        truth = [s.is_true for s in scores]

        metrics = _evaluate(truth, labels)

    return ModelResponse(scores=scores, metrics=metrics, meta=meta)
