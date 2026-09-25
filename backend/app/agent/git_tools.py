from app.agent.tool_registry import (
    Tool,
    ToolParameter,
    ToolRegistry,
)

from app.tools.git.status import get_repository_status
from app.tools.git.diff import get_repository_diff
from app.tools.git.history import get_commit_history
from app.tools.git.repository import get_repository_info
from app.tools.git.branch import create_branch


def create_git_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()

    # --------------------------------------------------
    # COMMON PARAMETERS
    # --------------------------------------------------

    repository_path_parameter = ToolParameter(
        name="repository_path",
        type="string",
        description="Absolute path to the local Git repository.",
        required=True,
    )

    branch_name_parameter = ToolParameter(
        name="branch_name",
        type="string",
        description="Name of the new Git branch.",
        required=True,
    )

    # --------------------------------------------------
    # READ TOOLS
    # --------------------------------------------------

    registry.register(
        Tool(
            name="repository_status",
            description=(
                "Get the current Git repository status, "
                "including staged, modified, deleted, and "
                "untracked files."
            ),
            function=get_repository_status,
            parameters=[
                repository_path_parameter,
            ],
            risk="read",
            requires_approval=False,
        )
    )

    registry.register(
        Tool(
            name="repository_diff",
            description=(
                "Get the current unstaged Git diff "
                "for the repository."
            ),
            function=get_repository_diff,
            parameters=[
                repository_path_parameter,
            ],
            risk="read",
            requires_approval=False,
        )
    )

    registry.register(
        Tool(
            name="repository_history",
            description=(
                "Get recent Git commit history for "
                "the repository."
            ),
            function=get_commit_history,
            parameters=[
                repository_path_parameter,
            ],
            risk="read",
            requires_approval=False,
        )
    )

    registry.register(
        Tool(
            name="repository_info",
            description=(
                "Get repository information including "
                "the current branch and Git remotes."
            ),
            function=get_repository_info,
            parameters=[
                repository_path_parameter,
            ],
            risk="read",
            requires_approval=False,
        )
    )

    # --------------------------------------------------
    # WRITE TOOLS
    # --------------------------------------------------

    registry.register(
        Tool(
            name="create_branch",
            description=(
                "Create a new Git branch and switch "
                "to that branch."
            ),
            function=create_branch,
            parameters=[
                repository_path_parameter,
                branch_name_parameter,
            ],
            risk="write",
            requires_approval=True,
        )
    )

    return registry