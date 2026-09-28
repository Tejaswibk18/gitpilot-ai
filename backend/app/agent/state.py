import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field


class AgentTask(BaseModel):
    id: str
    description: str

    status: Literal[
        "pending",
        "running",
        "completed",
        "failed",
        "waiting_approval",
        "rejected",
    ] = "pending"

    result: Any | None = None
    error: str | None = None


class ToolCall(BaseModel):
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    tool_name: str
    success: bool
    result: Any | None = None
    error: str | None = None


class ApprovalRequest(BaseModel):
    approval_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)

    risk: Literal["write", "destructive"]

    reason: str

    status: Literal[
        "pending",
        "approved",
        "rejected",
    ] = "pending"



class AgentState(BaseModel):
    user_request: str
    repository_path: str

    tasks: list[AgentTask] = Field(default_factory=list)

    tool_calls: list[ToolCall] = Field(default_factory=list)

    tool_results: list[ToolResult] = Field(default_factory=list)

    observations: list[dict[str, Any]] = Field(default_factory=list)

    approval_requests: list[ApprovalRequest] = Field(
        default_factory=list
    )

    current_task_id: str | None = None

    pending_tool_call: ToolCall | None = None

    status: Literal[
        "planning",
        "executing",
        "waiting_approval",
        "evaluating",
        "completed",
        "failed",
        "rejected",
    ] = "planning"

    final_response: str | None = None