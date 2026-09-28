from app.services.git_service import GitService


def commit_changes(repository_path: str, message: str) -> dict:
    git_service = GitService(repository_path)
    output = git_service.commit_changes(message)

    return {
        "repository_path": repository_path,
        "message": message,
        "output": output,
    }
