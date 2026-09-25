import json

from app.agent.state import AgentState, AgentTask
from app.agent.git_tools import create_git_tool_registry
from app.services.llm_service import LLMService


class Planner:

    def __init__(self):
        self.llm = LLMService()
        self.registry = create_git_tool_registry()

    def create_plan(self, state: AgentState) -> AgentState:

        tools = self.registry.get_schemas()

        system_prompt = """
You are the planning component of GitPilot AI.

Your job is to understand the user's Git/GitHub request
and create a plan using the available tools.

Rules:

1. Only use tools provided in the tool list.
2. Do not invent tool names.
3. Break the request into the smallest useful sequence of tasks.
4. Read-only inspection should happen before write operations.
5. Do not execute tools yourself.
6. Return ONLY valid JSON.

The JSON format must be:

{
    "tasks": [
        {
            "id": "tool_name",
            "description": "What this task should accomplish"
        }
    ]
}
"""

        user_prompt = f"""
User request:

{state.user_request}

Repository:

{state.repository_path}

Available tools:

{json.dumps(tools, indent=2)}
"""

        response = self.llm.generate(
            [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ]
        )

        try:
            plan = json.loads(response)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"LLM returned invalid JSON: {response}"
            ) from exc

        tasks = []

        for task in plan.get("tasks", []):

            tasks.append(
                AgentTask(
                    id=task["id"],
                    description=task["description"],
                )
            )

        if not tasks:
            raise ValueError(
                "LLM returned an empty execution plan."
            )

        state.tasks = tasks
        state.status = "executing"

        return state