from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.repository_manager import RepositoryManager
from app.services.conflict_service import ConflictService


router = APIRouter(
    prefix="/api/conflicts",
    tags=["Conflicts"],
)


class BaseConflictRequest(BaseModel):
    repository_path: str


class AttemptMergeRequest(BaseConflictRequest):
    source_branch: str
    target_branch: Optional[str] = None


class ConflictFileRequest(BaseConflictRequest):
    file_path: str


class ApplyResolutionRequest(BaseConflictRequest):
    file_path: str
    resolved_content: str


class CompleteMergeRequest(BaseConflictRequest):
    message: Optional[str] = None


@router.post("/attempt-merge")
def attempt_merge(request: AttemptMergeRequest):
    try:
        resolved = RepositoryManager.resolve_repository_path(request.repository_path)
        service = ConflictService(resolved)
        return service.attempt_merge(request.source_branch, request.target_branch)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/detect")
def detect_conflicts(request: BaseConflictRequest):
    try:
        resolved = RepositoryManager.resolve_repository_path(request.repository_path)
        service = ConflictService(resolved)
        conflicted_files = service.get_conflicted_files()
        return {
            "merge_in_progress": service.is_merge_in_progress(),
            "conflict_count": len(conflicted_files),
            "conflicted_files": conflicted_files,
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/details")
def conflict_details(request: ConflictFileRequest):
    try:
        resolved = RepositoryManager.resolve_repository_path(request.repository_path)
        service = ConflictService(resolved)
        return service.get_conflict_details(request.file_path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/resolve-ai")
def resolve_conflicts_ai(request: ConflictFileRequest):
    try:
        resolved = RepositoryManager.resolve_repository_path(request.repository_path)
        service = ConflictService(resolved)
        return service.generate_ai_resolution(request.file_path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/apply")
def apply_conflict_resolution(request: ApplyResolutionRequest):
    try:
        resolved = RepositoryManager.resolve_repository_path(request.repository_path)
        service = ConflictService(resolved)
        return service.apply_resolution(request.file_path, request.resolved_content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/complete")
def complete_merge(request: CompleteMergeRequest):
    try:
        resolved = RepositoryManager.resolve_repository_path(request.repository_path)
        service = ConflictService(resolved)
        return service.complete_merge(request.message)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/abort")
def abort_merge(request: BaseConflictRequest):
    try:
        resolved = RepositoryManager.resolve_repository_path(request.repository_path)
        service = ConflictService(resolved)
        return service.abort_merge()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
