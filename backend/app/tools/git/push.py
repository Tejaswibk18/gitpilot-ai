from app.services.git_service import GitService


def push_branch(repository_path: str, remote: str = "origin", branch_name: str | None = None) -> dict:
    git_service = GitService(repository_path)
    try:
        output = git_service.push_branch(remote=remote, branch_name=branch_name)
        return {
            "repository_path": repository_path,
            "remote": remote,
            "branch_name": branch_name or git_service.get_current_branch(),
            "output": output,
        }
    except RuntimeError as exc:
        err_msg = str(exc)
        if "Permission to" in err_msg or "403" in err_msg or "denied" in err_msg:
            raise RuntimeError(
                f"Push failed (Permission Denied 403): You do not have write access to push directly to '{remote}'. "
                "If this is an external/open-source repository (e.g. pydantic), you should fork the repository to your own GitHub account first."
            )
        raise exc
