from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.models.dependencies import get_predict_zero
from app.schemas import ModelRequest, ModelResponse

router = APIRouter(prefix="/tuned")


@router.post("/predict")
async def predict(
    requests: list[ModelRequest],
    predict_fn: Annotated[list[ModelResponse], Depends(get_predict_zero)],
) -> list[ModelResponse]:
    raise HTTPException(status_code=501, detail="tuned model predictions is not implemented yet")
