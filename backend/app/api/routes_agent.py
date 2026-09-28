import os
import uuid
from typing import Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.agent.agent import GitPilotAgent
from app.agent.state import AgentState
from app.services.repository_manager import RepositoryManager

router = APIRouter(
    prefix="/api/agent",
    tags=["Agent"],
)

# In-memory session store
AGENT_SESSIONS: Dict[str, AgentState] = {}
AGENT_INSTANCES: Dict[str, GitPilotAgent] = {}


class AgentRunRequest(BaseModel):
    user_request: str = Field(..., description="Prompt or command for GitPilot AI")
    target: str = Field(..., description="Local repository path OR GitHub URL / owner/repo slug")
    session_id: Optional[str] = Field(None, description="Existing session ID if continuing conversation")
    token: Optional[str] = Field(None, description="Optional GitHub Personal Access Token")


class AgentApproveRequest(BaseModel):
    session_id: str = Field(..., description="ID of the active agent session")
    approval_id: Optional[str] = Field(None, description="ID of the approval request")
    approved: bool = Field(..., description="True to approve execution, False to deny")


@router.post("/run")
def run_agent(request: AgentRunRequest):
    if request.token:
        os.environ["GITHUB_TOKEN"] = request.token

    try:
        resolved_path = RepositoryManager.resolve_repository_path(request.target)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    session_id = request.session_id or str(uuid.uuid4())

    if session_id in AGENT_INSTANCES:
        agent = AGENT_INSTANCES[session_id]
        state = AGENT_SESSIONS[session_id]
        state.user_request = request.user_request
        state.repository_path = resolved_path
    else:
        agent = GitPilotAgent()
        state = AgentState(
            user_request=request.user_request,
            repository_path=resolved_path,
            status="planning",
        )
        AGENT_INSTANCES[session_id] = agent

    try:
        updated_state = agent.gemini_agent.run(state)
        AGENT_SESSIONS[session_id] = updated_state

        return {
            "session_id": session_id,
            "status": updated_state.status,
            "repository_path": updated_state.repository_path,
            "tool_calls": [tc.model_dump() for tc in updated_state.tool_calls],
            "tool_results": [tr.model_dump() for tr in updated_state.tool_results],
            "approval_requests": [ar.model_dump() for ar in updated_state.approval_requests],
            "final_response": updated_state.final_response,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Agent execution error: {str(exc)}")


@router.post("/approve")
def approve_action(request: AgentApproveRequest):
    if request.session_id not in AGENT_SESSIONS:
        raise HTTPException(status_code=404, detail=f"Session '{request.session_id}' not found.")

    agent = AGENT_INSTANCES[request.session_id]
    state = AGENT_SESSIONS[request.session_id]

    if state.status != "waiting_approval":
        raise HTTPException(status_code=400, detail=f"Session is not waiting for approval (current status: {state.status}).")

    try:
        updated_state = agent.gemini_agent.resume_after_approval(
            state,
            approved=request.approved,
            approval_id=request.approval_id,
        )
        AGENT_SESSIONS[request.session_id] = updated_state

        return {
            "session_id": request.session_id,
            "status": updated_state.status,
            "repository_path": updated_state.repository_path,
            "tool_calls": [tc.model_dump() for tc in updated_state.tool_calls],
            "tool_results": [tr.model_dump() for tr in updated_state.tool_results],
            "approval_requests": [ar.model_dump() for ar in updated_state.approval_requests],
            "final_response": updated_state.final_response,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Approval execution error: {str(exc)}")


@router.get("/session/{session_id}")
def get_session_state(session_id: str):
    if session_id not in AGENT_SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found.")
    state = AGENT_SESSIONS[session_id]
    return {
        "session_id": session_id,
        "status": state.status,
        "repository_path": state.repository_path,
        "tool_calls": [tc.model_dump() for tc in state.tool_calls],
        "tool_results": [tr.model_dump() for tr in state.tool_results],
        "approval_requests": [ar.model_dump() for ar in state.approval_requests],
        "final_response": state.final_response,
    }
