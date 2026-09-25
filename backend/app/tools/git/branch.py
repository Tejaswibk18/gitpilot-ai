from app.services.git_service import GitService


def create_branch(
    repository_path: str,
    branch_name: str,
) -> dict:

    git = GitService(repository_path)

    current_branch = git.get_current_branch()

    new_branch = git.create_branch(
        branch_name
    )

    return {
        "previous_branch": current_branch,
        "current_branch": new_branch,
    }