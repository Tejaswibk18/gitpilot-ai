from app.services.repository_service import RepositoryService


def get_repository_info(repository_path: str) -> dict:

    service = RepositoryService(repository_path)

    info = service.get_repository_info()

    return info.model_dump()