from app.services.git_service import GitService


def checkout_branch(repository_path: str, branch_name: str) -> dict:
    git_service = GitService(repository_path)
    current_branch = git_service.checkout_branch(branch_name)

    return {
        "repository_path": repository_path,
        "current_branch": current_branch,
    }
