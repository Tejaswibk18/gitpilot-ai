from typing import Any
from app.services.conflict_service import ConflictService


def attempt_merge(
    repository_path: str,
    target_branch: str,
    source_branch: str,
) -> dict[str, Any]:
    service = ConflictService(repository_path)
    return service.attempt_merge(target_branch, source_branch)


def abort_merge(
    repository_path: str,
) -> dict[str, Any]:
    service = ConflictService(repository_path)
    return service.abort_merge()


def complete_merge(
    repository_path: str,
    message: str | None = None,
) -> dict[str, Any]:
    service = ConflictService(repository_path)
    return service.complete_merge(message)
