from typing import Optional
from fastapi import APIRouter, Cookie, HTTPException
from pydantic import BaseModel, Field

from app.services.github_service import GitHubService
from app.services.github_auth import get_session_token

router = APIRouter(prefix="/api/github", tags=["GitHub API"])
SESSION_COOKIE = "gitpilot_session"


class GitHubRepoRequest(BaseModel):
    repository_path: str = Field(..., description="Local repo path OR GitHub URL / slug")


class CreatePRRequest(GitHubRepoRequest):
    title: str
    body: str
    head_branch: str
    base_branch: str = "main"


class MergePRRequest(GitHubRepoRequest):
    pr_number: int
    commit_title: Optional[str] = None


class CreateIssueCommentRequest(GitHubRepoRequest):
    issue_number: int
    body: str


def _github_service(session_id: str | None) -> GitHubService:
    return GitHubService(token=get_session_token(session_id))


@router.post("/prs")
def list_prs(request: GitHubRepoRequest, gitpilot_session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
    try:
        gh = _github_service(gitpilot_session)
        slug = gh.extract_repo_slug(request.repository_path)
        return {"repo_slug": slug, "pull_requests": gh.list_pull_requests(slug)}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/pr/create")
def create_pr(request: CreatePRRequest, gitpilot_session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
    try:
        gh = _github_service(gitpilot_session)
        slug = gh.extract_repo_slug(request.repository_path)
        res = gh.create_pull_request(slug, request.title, request.body, request.head_branch, request.base_branch)
        return {"repo_slug": slug, "pull_request": res}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/pr/merge")
def merge_pr(request: MergePRRequest, gitpilot_session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
    try:
        gh = _github_service(gitpilot_session)
        slug = gh.extract_repo_slug(request.repository_path)
        res = gh.merge_pull_request(slug, request.pr_number, request.commit_title)
        return {"repo_slug": slug, "result": res}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/issues")
def list_issues(request: GitHubRepoRequest, gitpilot_session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
    try:
        gh = _github_service(gitpilot_session)
        slug = gh.extract_repo_slug(request.repository_path)
        return {"repo_slug": slug, "issues": gh.list_issues(slug)}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/issue/comment")
def create_issue_comment(request: CreateIssueCommentRequest, gitpilot_session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
    try:
        gh = _github_service(gitpilot_session)
        slug = gh.extract_repo_slug(request.repository_path)
        res = gh.create_issue_comment(slug, request.issue_number, request.body)
        return {"repo_slug": slug, "comment": res}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
