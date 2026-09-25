from app.services.git_service import GitService


def get_repository_diff(repository_path: str) -> dict:
    git = GitService(repository_path)

    return {
        "repository": repository_path,
        "diff": git.get_diff(),
    }