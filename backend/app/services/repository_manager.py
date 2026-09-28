import os
import re
from pathlib import Path
import subprocess
import httpx

from app.services.git_service import GitService

WORKSPACES_DIR = Path(__file__).resolve().parent.parent.parent / "workspaces"


class RepositoryManager:

    @staticmethod
    def is_github_url(target: str) -> bool:
        """
        Check if target string is a GitHub URL or owner/repo format.
        """
        target = target.strip()
        if target.startswith("http://") or target.startswith("https://") or target.startswith("git@"):
            return "github.com" in target or target.endswith(".git")
        if re.match(r"^[a-zA-Z0-9_\-]+/[a-zA-Z0-9_\.\-]+$", target):
            return True
        return False

    @staticmethod
    def validate_github_url(github_url: str) -> bool:
        """
        Validates if a GitHub repository URL/slug exists and is accessible.
        Uses git ls-remote or GitHub API check.
        """
        # Try git ls-remote (fastest and handles public/auth repos)
        result = subprocess.run(
            ["git", "ls-remote", github_url, "HEAD"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=10,
        )
        return result.returncode == 0

    @staticmethod
    def resolve_repository_path(target: str) -> str:
        """
        Resolves a target string (which could be a local path OR a GitHub URL/slug)
        to a local directory path. Clones the repository if it's a GitHub URL.
        """
        target = target.strip()

        # 1. If it's already an existing local directory on disk
        local_path = Path(target).resolve()
        if local_path.exists():
            if (local_path / ".git").exists():
                return str(local_path)
            else:
                raise ValueError(f"Local path '{target}' exists but is not a valid Git repository (missing .git directory).")

        # 2. If it's a GitHub URL or owner/repo slug
        if RepositoryManager.is_github_url(target):
            return RepositoryManager.clone_or_sync_github_repo(target)

        raise ValueError(f"Invalid local directory path or GitHub URL: '{target}'")

    @staticmethod
    def clone_or_sync_github_repo(github_target: str) -> str:
        """
        Clones a GitHub repo into backend/workspaces/<owner_repo>.
        If already cloned, verifies origin URL and fetches latest.
        """
        WORKSPACES_DIR.mkdir(parents=True, exist_ok=True)

        token = os.getenv("GITHUB_TOKEN")
        github_url = github_target.strip()
        if not (github_url.startswith("http") or github_url.startswith("git@")):
            if token and "@github.com" not in github_url:
                github_url = f"https://x-access-token:{token}@github.com/{github_url}.git"
            else:
                github_url = f"https://github.com/{github_url}.git"
        elif token and "https://github.com/" in github_url and "@github.com" not in github_url:
            github_url = github_url.replace("https://github.com/", f"https://x-access-token:{token}@github.com/")

        if not github_url.endswith(".git") and "github.com" in github_url:
            github_url = f"{github_url}.git"

        # Extract full 'owner/repo' slug for unique folder naming (e.g. octocat_Hello-World)
        match = re.search(r"github\.com[/:]([a-zA-Z0-9_\-]+/[a-zA-Z0-9_\.\-]+)", github_url)
        if match:
            slug = match.group(1).replace(".git", "")
        else:
            slug = github_target.strip().replace(".git", "")

        folder_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", slug)
        target_dir = WORKSPACES_DIR / folder_name

        # If workspace already exists, verify it's valid
        if target_dir.exists() and (target_dir / ".git").exists():
            # Check if remote URL matches
            try:
                git_service = GitService(str(target_dir))
                remotes = git_service.get_remotes()
                # Fetch latest updates
                subprocess.run(
                    ["git", "fetch", "--all"],
                    cwd=target_dir,
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
                return str(target_dir)
            except Exception:
                pass  # Re-clone if existing folder is corrupt

        # First, validate the GitHub URL before attempting clone
        if not RepositoryManager.validate_github_url(github_url):
            raise ValueError(f"GitHub repository '{github_target}' does not exist or is inaccessible.")

        # Clean up any broken target directory if it exists
        if target_dir.exists():
            import shutil
            shutil.rmtree(target_dir, ignore_errors=True)

        # Clone repository
        result = subprocess.run(
            ["git", "clone", github_url, str(target_dir)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60,
        )

        if result.returncode != 0:
            err_msg = result.stderr.strip() or result.stdout.strip()
            raise ValueError(f"Failed to clone GitHub repository '{github_url}': {err_msg}")

        return str(target_dir)
