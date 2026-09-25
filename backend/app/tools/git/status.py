from app.services.repository_service import RepositoryService


def get_repository_status(repository_path: str) -> dict:

    service = RepositoryService(repository_path)

    status = service.get_status()

    return status.model_dump()