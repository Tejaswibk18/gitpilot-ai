from typing import Optional
from app.services.github_service import GitHubService
from app.services.github_auth import get_workspace_token


def create_pull_request(
    repository_path: str,
    title: str,
    body: str,
    head_branch: str,
    base_branch: str = "main",
    token: Optional[str] = None,
) -> dict:
    github_service = GitHubService(token=token or get_workspace_token(repository_path))
    repo_slug = github_service.extract_repo_slug(repository_path)
    res = github_service.create_pull_request(
        repo_slug=repo_slug,
        title=title,
        body=body,
        head_branch=head_branch,
        base_branch=base_branch,
    )
    return {
        "repo_slug": repo_slug,
        "pr_number": res["number"],
        "html_url": res["html_url"],
        "title": res["title"],
        "head": head_branch,
        "base": base_branch,
    }


def list_pull_requests(
    repository_path: str,
    state: str = "open",
    token: Optional[str] = None,
) -> dict:
    github_service = GitHubService(token=token or get_workspace_token(repository_path))
    repo_slug = github_service.extract_repo_slug(repository_path)
    prs = github_service.list_pull_requests(repo_slug=repo_slug, state=state)
    return {
        "repo_slug": repo_slug,
        "pull_requests": prs,
    }


def merge_pull_request(
    repository_path: str,
    pr_number: int,
    commit_title: Optional[str] = None,
    token: Optional[str] = None,
) -> dict:
    github_service = GitHubService(token=token or get_workspace_token(repository_path))
    repo_slug = github_service.extract_repo_slug(repository_path)
    res = github_service.merge_pull_request(
        repo_slug=repo_slug,
        pr_number=pr_number,
        commit_title=commit_title,
    )
    return {
        "repo_slug": repo_slug,
        "pr_number": pr_number,
        "merged": res.get("merged", True),
        "message": res.get("message", "PR merged successfully"),
    }
