from app.services.repository_service import RepositoryService


def get_commit_history(
    repository_path: str,
    limit: int = 10,
) -> list[dict]:

    service = RepositoryService(repository_path)

    commits = service.get_commits(limit)

    return [
        commit.model_dump()
        for commit in commits
    ]