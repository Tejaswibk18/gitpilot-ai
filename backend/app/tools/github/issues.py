from typing import Optional
from app.services.github_service import GitHubService


def list_issues(
    repository_path: str,
    state: str = "open",
    token: Optional[str] = None,
) -> dict:
    github_service = GitHubService(token=token)
    repo_slug = github_service.extract_repo_slug(repository_path)
    issues = github_service.list_issues(repo_slug=repo_slug, state=state)
    return {
        "repo_slug": repo_slug,
        "issues": issues,
    }


def get_issue(
    repository_path: str,
    issue_number: int,
    token: Optional[str] = None,
) -> dict:
    github_service = GitHubService(token=token)
    repo_slug = github_service.extract_repo_slug(repository_path)
    issue = github_service.get_issue(repo_slug=repo_slug, issue_number=issue_number)
    return {
        "repo_slug": repo_slug,
        "issue": issue,
    }


def create_issue_comment(
    repository_path: str,
    issue_number: int,
    body: str,
    token: Optional[str] = None,
) -> dict:
    github_service = GitHubService(token=token)
    repo_slug = github_service.extract_repo_slug(repository_path)
    res = github_service.create_issue_comment(
        repo_slug=repo_slug,
        issue_number=issue_number,
        body=body,
    )
    return {
        "repo_slug": repo_slug,
        "issue_number": issue_number,
        "comment_id": res.get("id"),
        "html_url": res.get("html_url"),
    }
