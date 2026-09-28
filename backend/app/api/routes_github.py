from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.github_service import GitHubService


router = APIRouter(
    prefix="/api/github",
    tags=["GitHub API"],
)


class GitHubRepoRequest(BaseModel):
    repository_path: str = Field(..., description="Local repo path OR GitHub URL / slug")
    token: Optional[str] = Field(None, description="Optional GitHub Personal Access Token")


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


@router.post("/prs")
def list_prs(request: GitHubRepoRequest):
    try:
        gh = GitHubService(token=request.token)
        slug = gh.extract_repo_slug(request.repository_path)
        prs = gh.list_pull_requests(slug)
        return {"repo_slug": slug, "pull_requests": prs}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/pr/create")
def create_pr(request: CreatePRRequest):
    try:
        gh = GitHubService(token=request.token)
        slug = gh.extract_repo_slug(request.repository_path)
        res = gh.create_pull_request(
            repo_slug=slug,
            title=request.title,
            body=request.body,
            head_branch=request.head_branch,
            base_branch=request.base_branch,
        )
        return {"repo_slug": slug, "pull_request": res}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/pr/merge")
def merge_pr(request: MergePRRequest):
    try:
        gh = GitHubService(token=request.token)
        slug = gh.extract_repo_slug(request.repository_path)
        res = gh.merge_pull_request(
            repo_slug=slug,
            pr_number=request.pr_number,
            commit_title=request.commit_title,
        )
        return {"repo_slug": slug, "result": res}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/issues")
def list_issues(request: GitHubRepoRequest):
    try:
        gh = GitHubService(token=request.token)
        slug = gh.extract_repo_slug(request.repository_path)
        issues = gh.list_issues(slug)
        return {"repo_slug": slug, "issues": issues}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/issue/comment")
def create_issue_comment(request: CreateIssueCommentRequest):
    try:
        gh = GitHubService(token=request.token)
        slug = gh.extract_repo_slug(request.repository_path)
        res = gh.create_issue_comment(
            repo_slug=slug,
            issue_number=request.issue_number,
            body=request.body,
        )
        return {"repo_slug": slug, "comment": res}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
