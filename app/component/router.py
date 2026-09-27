from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_component
from app.api.schemas import Response
from app.interfaces import IDependency

router = APIRouter(prefix="/user")


@router.get(
    "/{path_param}/recommend",
    summary="Placeholder endpoint",
    description="PlaceHolder endpoint",
    responses={200: {"model": Response}},
)
async def get_recommendations(
    path_param: int,
    query_param: int = Query(default=5, ge=1, le=100),
    dependency: IDependency = Depends(get_component),
) -> Response:
    _ = await dependency.method()
    return Response(code=[path_param, query_param])
