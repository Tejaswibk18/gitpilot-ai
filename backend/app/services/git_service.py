from pathlib import Path
import subprocess


class GitService:

    def __init__(self, repository_path: str):
        self.repository_path = Path(repository_path).resolve()

        if not self.repository_path.exists():
            raise ValueError(
                f"Repository path does not exist: {self.repository_path}"
            )

        if not (self.repository_path / ".git").exists():
            raise ValueError(
                f"Not a Git repository: {self.repository_path}"
            )

    def _run_git(self, *args: str) -> str:
        result = subprocess.run(
            ["git", *args],
            cwd=self.repository_path,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        if result.returncode != 0:
            raise RuntimeError(
                result.stderr.strip()
            )

        return result.stdout.strip()

    def get_current_branch(self) -> str:
        return self._run_git(
            "branch",
            "--show-current"
        )

    def get_status_porcelain(self) -> str:
        return self._run_git(
            "status",
            "--porcelain=v1",
            "-z",
        )

    def get_diff(self) -> str:
        return self._run_git(
            "diff"
        )

    def get_staged_diff(self) -> str:
        return self._run_git(
            "diff",
            "--cached"
        )

    def get_log(self, limit: int = 10) -> str:
        return self._run_git(
            "log",
            f"-{limit}",
            "--pretty=format:%H|%h|%an|%ad|%s",
            "--date=iso",
        )

    def get_remotes(self) -> str:
        return self._run_git(
            "remote",
            "-v"
        )

    def create_branch(self, branch_name: str) -> str:
        if not branch_name.strip():
            raise ValueError("Branch name cannot be empty.")

        current_branch = self.get_current_branch()

        if branch_name == current_branch:
            raise ValueError(
                f"Already on branch '{branch_name}'."
            )

        existing_branches = self._run_git(
            "branch",
            "--format=%(refname:short)",
        ).splitlines()

        if branch_name in existing_branches:
            raise ValueError(
                f"Branch '{branch_name}' already exists."
            )

        self._run_git(
            "switch",
            "-c",
            branch_name,
        )

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
        out = self._run_git("commit", "-m", message)
        return out

    def push_branch(self, remote: str = "origin", branch_name: str | None = None) -> str:
        if not branch_name:
            branch_name = self.get_current_branch()
        out = self._run_git("push", "-u", remote, branch_name)
        return out