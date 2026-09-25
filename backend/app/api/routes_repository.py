from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.tools.git.status import get_repository_status
from app.tools.git.diff import get_repository_diff
from app.tools.git.repository import get_repository_info
from app.tools.git.history import get_commit_history


router = APIRouter(
    prefix="/api/repository",
    tags=["Repository"],
)


class RepositoryRequest(BaseModel):
    repository_path: str


@router.post("/info")
def repository_info(request: RepositoryRequest):

    try:
        return get_repository_info(
            request.repository_path
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except RuntimeError as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@router.post("/status")
def repository_status(request: RepositoryRequest):

    try:
        return get_repository_status(
            request.repository_path
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except RuntimeError as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@router.post("/diff")
def repository_diff(request: RepositoryRequest):

    try:
        return get_repository_diff(
            request.repository_path
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except RuntimeError as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@router.post("/history")
def repository_history(
    request: RepositoryRequest,
    limit: int = 10,
):

    try:
        return get_commit_history(
            request.repository_path,
            limit=limit,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except RuntimeError as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )