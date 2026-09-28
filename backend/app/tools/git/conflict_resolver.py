from typing import Any
from app.services.conflict_service import ConflictService


def detect_merge_conflicts(
    repository_path: str,
) -> dict[str, Any]:
    service = ConflictService(repository_path)
    conflicted_files = service.get_conflicted_files()
    in_progress = service.is_merge_in_progress()
    return {
        "merge_in_progress": in_progress,
        "conflict_count": len(conflicted_files),
        "conflicted_files": conflicted_files,
    }


def get_conflict_details(
    repository_path: str,
    file_path: str,
) -> dict[str, Any]:
    service = ConflictService(repository_path)
    return service.get_conflict_details(file_path)


def resolve_conflicts_ai(
    repository_path: str,
    file_path: str,
) -> dict[str, Any]:
    service = ConflictService(repository_path)
    return service.generate_ai_resolution(file_path)


def apply_conflict_resolution(
    repository_path: str,
    file_path: str,
    resolved_content: str,
) -> dict[str, Any]:
    service = ConflictService(repository_path)
    return service.apply_resolution(file_path, resolved_content)
