from fastapi import APIRouter, Depends

from app.interfaces import IModel
from app.model.dependencies import get_model
from app.model.schemas import Request, Response

# Not mounted in app_factory yet. When wiring it up, include via include_router
# under /api/v1 with Depends(require_bearer) so Prometheus path templating works.
router = APIRouter(prefix="/model")


@router.post(
    "/predict",
    summary="Model prediction",
    description="Run prediction on the configured model.",
    responses={200: {"model": Response}},
)
async def predict(request: Request, model: IModel = Depends(get_model)) -> Response:
    return Response(predictions=model.predict(request))
