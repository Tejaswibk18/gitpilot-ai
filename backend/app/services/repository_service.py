from app.models.repository import (
    RepositoryInfo,
    RepositoryStatus,
    CommitInfo,
    RemoteInfo,
)

from app.services.git_service import GitService


class RepositoryService:

    def __init__(self, repository_path: str):
        self.git = GitService(repository_path)

    def get_status(self) -> RepositoryStatus:

        branch = self.git.get_current_branch()
        raw_status = self.git.get_status_porcelain()

        staged = []
        modified = []
        deleted = []
        untracked = []

        entries = raw_status.split("\x00")

        for entry in entries:

            if not entry:
                continue

            if len(entry) < 3:
                continue

            index_status = entry[0]
            working_status = entry[1]
            filename = entry[3:]

            # Untracked file
            if index_status == "?" and working_status == "?":
                untracked.append(filename)
                continue

            # Staged changes
            if index_status != " ":

                if index_status == "D":
                    deleted.append(filename)

                else:
                    staged.append(filename)

            # Unstaged changes
            if working_status != " ":

                if working_status == "D":
                    deleted.append(filename)

                elif working_status == "M":
                    modified.append(filename)

        return RepositoryStatus(
            branch=branch,
            clean=not entries or all(not entry for entry in entries),
            staged=staged,
            modified=modified,
            deleted=deleted,
            untracked=untracked,
        )

    def get_repository_info(self) -> RepositoryInfo:

        branch = self.git.get_current_branch()
        raw_remotes = self.git.get_remotes()

        remotes = {}

        for line in raw_remotes.splitlines():

            parts = line.split() 

            if len(parts) < 3:
                continue

            name = parts[0]
            url = parts[1]
            operation = parts[2].strip("()")

            if name not in remotes:
                remotes[name] = {
                    "fetch_url": "",
                    "push_url": "",
                }

            if operation == "fetch":
                remotes[name]["fetch_url"] = url

            elif operation == "push":
                remotes[name]["push_url"] = url

        remote_models = [
            RemoteInfo(
                name=name,
                fetch_url=data["fetch_url"],
                push_url=data["push_url"],
            )
            for name, data in remotes.items()
        ]

        return RepositoryInfo(
            path=str(self.git.repository_path),
            branch=branch,
            remotes=remote_models,
        )

    def get_commits(self, limit: int = 10) -> list[CommitInfo]:

        raw_log = self.git.get_log(limit)

        if not raw_log:
            return []

        commits = []

        for line in raw_log.splitlines():

            parts = line.split("|", 4)

            if len(parts) != 5:
                continue

            commit_hash, short_hash, author, date, message = parts

            commits.append(
                CommitInfo(
                    hash=commit_hash,
                    short_hash=short_hash,
                    author=author,
                    date=date,
                    message=message,
                )
            )

        return commits