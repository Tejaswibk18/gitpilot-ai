import os
import re
from typing import Any, Dict, List, Optional
import httpx
from dotenv import load_dotenv

from app.services.git_service import GitService
from app.services.repository_manager import RepositoryManager

load_dotenv()


class GitHubService:

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

    @staticmethod
    def extract_repo_slug(target_path_or_url: str) -> str:
        """
        Extracts 'owner/repo' slug from a local path (via git remotes) or a GitHub URL/slug.
        """
        target = target_path_or_url.strip()

        # If it's a slug like owner/repo
        if re.match(r"^[a-zA-Z0-9_\-]+/[a-zA-Z0-9_\.\-]+$", target):
            return target.replace(".git", "")

        # If it's a GitHub URL
        if "github.com" in target:
            match = re.search(r"github\.com[/:]([a-zA-Z0-9_\-]+/[a-zA-Z0-9_\.\-]+)", target)
            if match:
                return match.group(1).replace(".git", "")

        # Try resolving via local git remotes
        try:
            resolved_path = RepositoryManager.resolve_repository_path(target)
            git_service = GitService(resolved_path)
            remotes = git_service.get_remotes()
            match = re.search(r"github\.com[/:]([a-zA-Z0-9_\-]+/[a-zA-Z0-9_\.\-]+)", remotes)
            if match:
                return match.group(1).replace(".git", "")
        except Exception:
            pass

        raise ValueError(f"Could not extract GitHub repository slug ('owner/repo') from: '{target}'")

    def _client(self) -> httpx.Client:
        return httpx.Client(headers=self.headers, timeout=15.0)

    def _check_rate_limit_error(self, res: httpx.Response):
        """
        Raises a user-friendly error message if GitHub API rate limit is exceeded.
        """
        if res.status_code in (403, 429) or res.headers.get("x-ratelimit-remaining") == "0":
            try:
                body = res.json()
                detail = body.get("message", "") if isinstance(body, dict) else str(body)
            except Exception:
                detail = res.text

            detail_lower = detail.lower()
            if "rate limit" in detail_lower or "secondary rate limit" in detail_lower or res.headers.get("x-ratelimit-remaining") == "0":
                raise RuntimeError(
                    "GitHub API Rate Limit Exceeded (60 req/hr for unauthenticated IPs). "
                    "Please configure a GITHUB_TOKEN in your .env file or UI settings to get 5,000 req/hr."
                )

        if res.status_code not in (200, 201):
            try:
                body = res.json()
                err_msg = body.get("message", res.text) if isinstance(body, dict) else res.text
            except Exception:
                err_msg = res.text
            raise RuntimeError(f"GitHub API Error ({res.status_code}): {err_msg}")

    def create_pull_request(
        self,
        repo_slug: str,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str = "main",
    ) -> Dict[str, Any]:
        """
        Creates a GitHub Pull Request.
        """
        url = f"{self.base_url}/repos/{repo_slug}/pulls"
        payload = {
            "title": title,
            "body": body,
            "head": head_branch,
            "base": base_branch,
        }

        with self._client() as client:
            res = client.post(url, json=payload)
            self._check_rate_limit_error(res)
            return res.json()

    def list_pull_requests(
        self,
        repo_slug: str,
        state: str = "open",
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Lists pull requests for a repository.
        """
        url = f"{self.base_url}/repos/{repo_slug}/pulls?state={state}&per_page={limit}"

        with self._client() as client:
            res = client.get(url)
            self._check_rate_limit_error(res)
            prs = res.json()
            return [
                {
                    "number": pr["number"],
                    "title": pr["title"],
                    "state": pr["state"],
                    "user": pr["user"]["login"],
                    "html_url": pr["html_url"],
                    "head_branch": pr["head"]["ref"],
                    "base_branch": pr["base"]["ref"],
                    "created_at": pr["created_at"],
                }
                for pr in prs
            ]

    def merge_pull_request(
        self,
        repo_slug: str,
        pr_number: int,
        commit_title: Optional[str] = None,
        merge_method: str = "merge",
    ) -> Dict[str, Any]:
        """
        Merges a pull request.
        """
        url = f"{self.base_url}/repos/{repo_slug}/pulls/{pr_number}/merge"
        payload: Dict[str, Any] = {"merge_method": merge_method}
        if commit_title:
            payload["commit_title"] = commit_title

        with self._client() as client:
            res = client.put(url, json=payload)
            self._check_rate_limit_error(res)
            return res.json()

    def list_issues(
        self,
        repo_slug: str,
        state: str = "open",
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Lists issues for a repository (excluding pull requests).
        """
        url = f"{self.base_url}/repos/{repo_slug}/issues?state={state}&per_page={limit}"

        with self._client() as client:
            res = client.get(url)
            self._check_rate_limit_error(res)
            items = res.json()
            # Filter out PRs (GitHub API returns PRs as issues unless filtered)
            issues = [item for item in items if "pull_request" not in item]
            return [
                {
                    "number": issue["number"],
                    "title": issue["title"],
                    "state": issue["state"],
                    "user": issue["user"]["login"],
                    "body": issue.get("body") or "",
                    "html_url": issue["html_url"],
                    "comments_count": issue["comments"],
                    "created_at": issue["created_at"],
                }
                for issue in issues
            ]

    def get_issue(
        self,
        repo_slug: str,
        issue_number: int,
    ) -> Dict[str, Any]:
        """
        Gets details of a specific issue.
        """
        url = f"{self.base_url}/repos/{repo_slug}/issues/{issue_number}"

        with self._client() as client:
            res = client.get(url)
            self._check_rate_limit_error(res)
            issue = res.json()
            return {
                "number": issue["number"],
                "title": issue["title"],
                "state": issue["state"],
                "user": issue["user"]["login"],
                "body": issue.get("body") or "",
                "html_url": issue["html_url"],
                "created_at": issue["created_at"],
            }

    def create_issue_comment(
        self,
        repo_slug: str,
        issue_number: int,
        body: str,
    ) -> Dict[str, Any]:
        """
        Creates a comment on an issue or PR.
        """
        url = f"{self.base_url}/repos/{repo_slug}/issues/{issue_number}/comments"
        payload = {"body": body}

        with self._client() as client:
            res = client.post(url, json=payload)
            self._check_rate_limit_error(res)
            return res.json()
