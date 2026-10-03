from typing import Annotated

from fastapi import APIRouter, Depends

from app.models.dependencies import get_predict_zero
from app.schemas import ModelRequest, ModelResponse

router = APIRouter(prefix="/zero")


@router.post("/predict")
async def predict(
    requests: list[ModelRequest],
    predict_fn: Annotated[list[ModelResponse], Depends(get_predict_zero)],
) -> ModelResponse:
    return predict_fn(requests)
