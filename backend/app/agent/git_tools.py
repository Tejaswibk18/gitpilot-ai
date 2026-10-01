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
from app.tools.git.commit import commit_changes
from app.tools.git.checkout import checkout_branch
from app.tools.git.push import push_branch

from app.tools.github.pull_request import (
    create_pull_request,
    list_pull_requests,
    merge_pull_request,
)
from app.tools.github.issues import (
    list_issues,
    get_issue,
    create_issue_comment,
)
from app.tools.git.merge import (
    attempt_merge,
    abort_merge,
    complete_merge,
)
from app.tools.git.conflict_resolver import (
    detect_merge_conflicts,
    get_conflict_details,
    resolve_conflicts_ai,
    apply_conflict_resolution,
)


def create_git_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()

    # --------------------------------------------------
    # COMMON PARAMETERS
    # --------------------------------------------------

    repository_path_parameter = ToolParameter(
        name="repository_path",
        type="string",
        description="Absolute path to local Git repository OR GitHub URL / owner/repo slug.",
        required=True,
    )

    branch_name_parameter = ToolParameter(
        name="branch_name",
        type="string",
        description="Name of the Git branch.",
        required=True,
    )

    commit_message_parameter = ToolParameter(
        name="message",
        type="string",
        description="Commit message describing the changes.",
        required=True,
    )

    remote_name_parameter = ToolParameter(
        name="remote",
        type="string",
        description="Remote repository name (default 'origin').",
        required=False,
    )

    # GitHub Parameters
    pr_title_parameter = ToolParameter(
        name="title",
        type="string",
        description="Title of the Pull Request or Issue.",
        required=True,
    )

    pr_body_parameter = ToolParameter(
        name="body",
        type="string",
        description="Detailed description body of the Pull Request or Issue comment.",
        required=True,
    )

    head_branch_parameter = ToolParameter(
        name="head_branch",
        type="string",
        description="The name of the branch where your changes are implemented.",
        required=True,
    )

    base_branch_parameter = ToolParameter(
        name="base_branch",
        type="string",
        description="The name of the branch you want the changes pulled into (default 'main').",
        required=False,
    )

    pr_number_parameter = ToolParameter(
        name="pr_number",
        type="integer",
        description="The number of the Pull Request.",
        required=True,
    )

    issue_number_parameter = ToolParameter(
        name="issue_number",
        type="integer",
        description="The number of the GitHub Issue.",
        required=True,
    )

    file_path_parameter = ToolParameter(
        name="file_path",
        type="string",
        description="Relative path of the file in the repository.",
        required=True,
    )

    source_branch_parameter = ToolParameter(
        name="source_branch",
        type="string",
        description="Source branch to merge from.",
        required=True,
    )

    target_branch_parameter = ToolParameter(
        name="target_branch",
        type="string",
        description="Target branch to merge into.",
        required=True,
    )

    resolved_content_parameter = ToolParameter(
        name="resolved_content",
        type="string",
        description="The fully resolved content of the conflicted file with markers removed.",
        required=True,
    )

    # --------------------------------------------------
    # READ GIT & GITHUB TOOLS (NO APPROVAL NEEDED)
    # --------------------------------------------------

    registry.register(
        Tool(
            name="repository_status",
            description="Get current Git status including staged, modified, deleted, and untracked files.",
            function=get_repository_status,
            parameters=[repository_path_parameter],
            risk="read",
            requires_approval=False,
        )
    )

    registry.register(
        Tool(
            name="repository_diff",
            description="Get current unstaged Git diff for the repository.",
            function=get_repository_diff,
            parameters=[repository_path_parameter],
            risk="read",
            requires_approval=False,
        )
    )

    registry.register(
        Tool(
            name="repository_history",
            description="Get recent Git commit history.",
            function=get_commit_history,
            parameters=[repository_path_parameter],
            risk="read",
            requires_approval=False,
        )
    )

    registry.register(
        Tool(
            name="repository_info",
            description="Get repository info including current branch and remotes.",
            function=get_repository_info,
            parameters=[repository_path_parameter],
            risk="read",
            requires_approval=False,
        )
    )

    registry.register(
        Tool(
            name="list_pull_requests",
            description="List open or closed Pull Requests on GitHub.",
            function=list_pull_requests,
            parameters=[repository_path_parameter],
            risk="read",
            requires_approval=False,
        )
    )

    registry.register(
        Tool(
            name="list_issues",
            description="List open or closed Issues on GitHub.",
            function=list_issues,
            parameters=[repository_path_parameter],
            risk="read",
            requires_approval=False,
        )
    )

    registry.register(
        Tool(
            name="get_issue",
            description="Get details of a specific GitHub Issue by issue_number.",
            function=get_issue,
            parameters=[repository_path_parameter, issue_number_parameter],
            risk="read",
            requires_approval=False,
        )
    )

    registry.register(
        Tool(
            name="detect_merge_conflicts",
            description="Detect currently active merge conflicts in the repository.",
            function=detect_merge_conflicts,
            parameters=[repository_path_parameter],
            risk="read",
            requires_approval=False,
        )
    )

    registry.register(
        Tool(
            name="get_conflict_details",
            description="Get parsed conflict markers and content for a specific conflicted file.",
            function=get_conflict_details,
            parameters=[repository_path_parameter, file_path_parameter],
            risk="read",
            requires_approval=False,
        )
    )

    registry.register(
        Tool(
            name="resolve_conflicts_ai",
            description="Ask Gemini AI to analyze conflict markers and synthesize a smart resolution.",
            function=resolve_conflicts_ai,
            parameters=[repository_path_parameter, file_path_parameter],
            risk="read",
            requires_approval=False,
        )
    )

    # --------------------------------------------------
    # WRITE GIT & GITHUB TOOLS (REQUIRE HITL APPROVAL)
    # --------------------------------------------------

    registry.register(
        Tool(
            name="attempt_merge",
            description="Attempt to merge source_branch into target_branch.",
            function=attempt_merge,
            parameters=[repository_path_parameter, source_branch_parameter, target_branch_parameter],
            risk="write",
            requires_approval=True,
        )
    )

    registry.register(
        Tool(
            name="apply_conflict_resolution",
            description="Write AI-resolved or user-resolved content to a conflicted file and stage it.",
            function=apply_conflict_resolution,
            parameters=[repository_path_parameter, file_path_parameter, resolved_content_parameter],
            risk="write",
            requires_approval=True,
        )
    )

    registry.register(
        Tool(
            name="complete_merge",
            description="Complete an in-progress merge commit once all conflicts are resolved.",
            function=complete_merge,
            parameters=[repository_path_parameter, commit_message_parameter],
            risk="write",
            requires_approval=True,
        )
    )

    registry.register(
        Tool(
            name="abort_merge",
            description="Abort an in-progress Git merge and restore working tree state.",
            function=abort_merge,
            parameters=[repository_path_parameter],
            risk="write",
            requires_approval=True,
        )
    )

    registry.register(
        Tool(
            name="create_branch",
            description="Create a new Git branch and switch to it.",
            function=create_branch,
            parameters=[repository_path_parameter, branch_name_parameter],
            risk="write",
            requires_approval=True,
        )
    )

    registry.register(
        Tool(
            name="checkout_branch",
            description="Switch to an existing Git branch.",
            function=checkout_branch,
            parameters=[repository_path_parameter, branch_name_parameter],
            risk="write",
            requires_approval=False,
        )
    )

    registry.register(
        Tool(
            name="commit_changes",
            description="Commit staged/modified changes with a commit message.",
            function=commit_changes,
            parameters=[repository_path_parameter, commit_message_parameter],
            risk="write",
            requires_approval=True,
        )
    )

    registry.register(
        Tool(
            name="push_branch",
            description="Push local branch commits to remote repository on GitHub.",
            function=push_branch,
            parameters=[repository_path_parameter, remote_name_parameter, branch_name_parameter],
            risk="write",
            requires_approval=True,
        )
    )

    registry.register(
        Tool(
            name="create_pull_request",
            description="Create a new GitHub Pull Request for a branch.",
            function=create_pull_request,
            parameters=[
                repository_path_parameter,
                pr_title_parameter,
                pr_body_parameter,
                head_branch_parameter,
                base_branch_parameter,
            ],
            risk="write",
            requires_approval=True,
        )
    )

    registry.register(
        Tool(
            name="merge_pull_request",
            description="Merge a Pull Request on GitHub.",
            function=merge_pull_request,
            parameters=[repository_path_parameter, pr_number_parameter],
            risk="write",
            requires_approval=True,
        )
    )

    registry.register(
        Tool(
            name="create_issue_comment",
            description="Add a comment to a GitHub Issue or Pull Request.",
            function=create_issue_comment,
            parameters=[repository_path_parameter, issue_number_parameter, pr_body_parameter],
            risk="write",
            requires_approval=True,
        )
    )

    return registry