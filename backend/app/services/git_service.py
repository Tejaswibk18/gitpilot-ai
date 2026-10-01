from pathlib import Path
import os
import subprocess
from typing import Optional

from app.services.github_auth import get_workspace_token


class GitService:

    def __init__(self, repository_path: str, token: Optional[str] = None):
        self.repository_path = Path(repository_path).resolve()
        self.token = token or get_workspace_token(str(self.repository_path))

        if not self.repository_path.exists():
            raise ValueError(f"Repository path does not exist: {self.repository_path}")
        if not (self.repository_path / ".git").exists():
            raise ValueError(f"Not a Git repository: {self.repository_path}")

    def _env(self) -> dict[str, str]:
        env = os.environ.copy()
        if self.token:
            env["GIT_CONFIG_COUNT"] = "1"
            env["GIT_CONFIG_KEY_0"] = "http.extraHeader"
            env["GIT_CONFIG_VALUE_0"] = f"Authorization: Bearer {self.token}"
        return env

    def _run_git(self, *args: str) -> str:
        result = subprocess.run(
            ["git", *args],
            cwd=self.repository_path,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=self._env(),
        )
        if result.returncode != 0:
            error_msg = result.stderr.strip() or result.stdout.strip()
            raise RuntimeError(error_msg)
        return result.stdout.strip()

    def get_current_branch(self) -> str:
        return self._run_git("branch", "--show-current")

    def get_status_porcelain(self) -> str:
        return self._run_git("status", "--porcelain=v1", "-z")

    def get_diff(self) -> str:
        return self._run_git("diff")

    def get_staged_diff(self) -> str:
        return self._run_git("diff", "--cached")

    def get_log(self, limit: int = 10) -> str:
        return self._run_git("log", f"-{limit}", "--pretty=format:%H|%h|%an|%ad|%s", "--date=iso")

    def get_remotes(self) -> str:
        return self._run_git("remote", "-v")

    def create_branch(self, branch_name: str) -> str:
        if not branch_name.strip():
            raise ValueError("Branch name cannot be empty.")
        current_branch = self.get_current_branch()
        if branch_name == current_branch:
            raise ValueError(f"Already on branch '{branch_name}'.")
        existing_branches = self._run_git("branch", "--format=%(refname:short)").splitlines()
        if branch_name in existing_branches:
            raise ValueError(f"Branch '{branch_name}' already exists.")
        self._run_git("switch", "-c", branch_name)
        return self.get_current_branch()

    def checkout_branch(self, branch_name: str) -> str:
        if not branch_name.strip():
            raise ValueError("Branch name cannot be empty.")
        self._run_git("checkout", branch_name)
        return self.get_current_branch()

    def stage_files(self, files: list[str] | str = ".") -> str:
        if isinstance(files, str):
            files = [files]
        self._run_git("add", *files)
        return "Files staged successfully."

    def commit_changes(self, message: str) -> str:
        if not message.strip():
            raise ValueError("Commit message cannot be empty.")
        return self._run_git("commit", "-m", message)

    def push_branch(self, remote: str = "origin", branch_name: str | None = None) -> str:
        if not branch_name:
            result = subprocess.run(
                ["git", "symbolic-ref", "--short", "HEAD"],
                cwd=self.repository_path,
                capture_output=True,
                text=True,
                encoding="utf-8",
                env=self._env(),
            )
            branch_name = result.stdout.strip() if result.returncode == 0 and result.stdout.strip() else "HEAD"

        if branch_name == "HEAD":
            raise RuntimeError("Repository has no commits yet. Please make at least one commit before pushing.")

        return self._run_git("push", "-u", remote, branch_name)
