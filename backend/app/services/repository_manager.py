import os
import re
import hashlib
from pathlib import Path
import subprocess
from typing import Optional

from app.services.git_service import GitService
from app.services.github_auth import get_workspace_token, set_workspace_token

WORKSPACES_DIR = Path(os.getenv("WORKSPACE_ROOT", Path(__file__).resolve().parent.parent.parent / "workspaces"))


def _git_env(token: Optional[str] = None) -> dict[str, str]:
    env = os.environ.copy()
    if token:
        # Pass the OAuth token through Git configuration environment variables so it
        # is not persisted in .git/config or exposed in the git command arguments.
        env["GIT_CONFIG_COUNT"] = "1"
        env["GIT_CONFIG_KEY_0"] = "http.extraHeader"
        env["GIT_CONFIG_VALUE_0"] = f"Authorization: Bearer {token}"
    return env


class RepositoryManager:

    @staticmethod
    def is_github_url(target: str) -> bool:
        target = target.strip()
        if target.startswith(("http://", "https://", "git@")):
            return "github.com" in target or target.endswith(".git")
        return bool(re.match(r"^[a-zA-Z0-9_\-]+/[a-zA-Z0-9_\.\-]+$", target))

    @staticmethod
    def validate_github_url(github_url: str, token: Optional[str] = None) -> bool:
        result = subprocess.run(
            ["git", "ls-remote", github_url, "HEAD"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=10,
            env=_git_env(token),
        )
        return result.returncode == 0

    @staticmethod
    def resolve_repository_path(target: str, token: Optional[str] = None, workspace_namespace: Optional[str] = None) -> str:
        target = target.strip()
        local_path = Path(target).resolve()
        if local_path.exists():
            if (local_path / ".git").exists():
                return str(local_path)
            raise ValueError(
                f"Local path '{target}' exists but is not a valid Git repository (missing .git directory)."
            )

        if RepositoryManager.is_github_url(target):
            return RepositoryManager.clone_or_sync_github_repo(target, token=token, workspace_namespace=workspace_namespace)

        raise ValueError(f"Invalid local directory path or GitHub URL: '{target}'")

    @staticmethod
    def clone_or_sync_github_repo(github_target: str, token: Optional[str] = None, workspace_namespace: Optional[str] = None) -> str:
        WORKSPACES_DIR.mkdir(parents=True, exist_ok=True)
        github_url = github_target.strip()

        if not (github_url.startswith("http") or github_url.startswith("git@")):
            github_url = f"https://github.com/{github_url}.git"
        elif not github_url.endswith(".git") and "github.com" in github_url:
            github_url = f"{github_url}.git"

        match = re.search(r"github\.com[/:]([a-zA-Z0-9_\-]+/[a-zA-Z0-9_\.\-]+)", github_url)
        if not match:
            raise ValueError(f"Invalid GitHub repository target: '{github_target}'")
        slug = match.group(1).replace(".git", "")

        folder_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", slug)
        if workspace_namespace:
            namespace = hashlib.sha256(workspace_namespace.encode()).hexdigest()[:16]
            folder_name = f"{namespace}_{folder_name}"
        target_dir = WORKSPACES_DIR / folder_name

        if target_dir.exists() and (target_dir / ".git").exists():
            try:
                GitService(str(target_dir))
                subprocess.run(
                    ["git", "fetch", "--all"],
                    cwd=target_dir,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    env=_git_env(token or get_workspace_token(str(target_dir))),
                )
                if token:
                    set_workspace_token(str(target_dir), token)
                return str(target_dir)
            except Exception:
                pass

        if not RepositoryManager.validate_github_url(github_url, token=token):
            raise ValueError(
                f"GitHub repository '{github_target}' does not exist or is inaccessible. "
                "For a private repository, connect your GitHub account first."
            )

        if target_dir.exists():
            import shutil
            shutil.rmtree(target_dir, ignore_errors=True)

        result = subprocess.run(
            ["git", "clone", github_url, str(target_dir)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60,
            env=_git_env(token),
        )

        if result.returncode != 0:
            err_msg = result.stderr.strip() or result.stdout.strip()
            raise ValueError(f"Failed to clone GitHub repository '{github_target}': {err_msg}")

        if token:
            set_workspace_token(str(target_dir), token)

        return str(target_dir)
