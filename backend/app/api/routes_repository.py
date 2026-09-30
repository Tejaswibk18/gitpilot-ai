from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.tools.git.status import get_repository_status
from app.tools.git.diff import get_repository_diff
from app.tools.git.repository import get_repository_info
from app.tools.git.history import get_commit_history
from app.services.repository_manager import RepositoryManager
from app.services.git_service import GitService
from app.services.llm_service import LLMService


router = APIRouter(
    prefix="/api/repository",
    tags=["Repository"],
)


class RepositoryRequest(BaseModel):
    repository_path: str


@router.post("/info")
def repository_info(request: RepositoryRequest):
    try:
        resolved = RepositoryManager.resolve_repository_path(request.repository_path)
        return get_repository_info(resolved)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/status")
def repository_status(request: RepositoryRequest):
    try:
        resolved = RepositoryManager.resolve_repository_path(request.repository_path)
        return get_repository_status(resolved)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/diff")
def repository_diff(request: RepositoryRequest):
    try:
        resolved = RepositoryManager.resolve_repository_path(request.repository_path)
        return get_repository_diff(resolved)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/history")
def repository_history(
    request: RepositoryRequest,
    limit: int = 10,
):
    try:
        resolved = RepositoryManager.resolve_repository_path(request.repository_path)
        return get_commit_history(resolved, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/staged-diff")
def repository_staged_diff(request: RepositoryRequest):
    """Returns the staged diff (git diff --cached) for commit message generation."""
    try:
        resolved = RepositoryManager.resolve_repository_path(request.repository_path)
        git = GitService(resolved)
        diff = git.get_staged_diff()
        return {"staged_diff": diff or ""}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/suggest-commit")
def suggest_commit_message(request: RepositoryRequest):
    """Uses Gemini AI to generate a Conventional Commit message from the staged diff."""
    try:
        resolved = RepositoryManager.resolve_repository_path(request.repository_path)
        git = GitService(resolved)
        staged_diff = git.get_staged_diff()

        if not staged_diff or not staged_diff.strip():
            raise HTTPException(
                status_code=400,
                detail="No staged changes found. Stage your files with 'git add' before generating a commit message."
            )

        llm = LLMService()
        prompt = f"""You are an expert software engineer writing a Git commit message.

Analyze the following staged diff and write a commit message following the Conventional Commits specification:
- Format: <type>(<optional scope>): <short summary> (max 72 chars)
- Body: Explain WHY the change was made, not what (2-3 sentences max, wrap at 72 chars)
- Use types: feat, fix, refactor, docs, style, test, chore, perf, ci, build

Rules:
- Summary must be concise and imperative tense (e.g., "add login validation" not "added")
- Do NOT include any markdown, code blocks, or extra commentary
- Output ONLY the raw commit message (title + blank line + body if needed)

Staged diff:
```
{staged_diff[:6000]}
```

Write the commit message now:"""

        message = llm.generate([{"role": "user", "content": prompt}])
        message = message.strip()

        return {
            "commit_message": message,
            "staged_diff_preview": staged_diff[:800] + ("..." if len(staged_diff) > 800 else ""),
        }
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))