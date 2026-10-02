from typing import Annotated

from fastapi import APIRouter, Depends

from app.models.zero import PredictFn, get_predict
from app.schemas import Document, ModelResponse

router = APIRouter(prefix="/model")


@router.post("/predict")
async def predict(request: Document, predict_fn: Annotated[PredictFn, Depends(get_predict)]) -> ModelResponse:
    rsp, _ = predict_fn([request])
    return rsp
