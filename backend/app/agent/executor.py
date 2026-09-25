from app.agent.state import AgentState, ToolCall, ToolResult
from app.agent.git_tools import create_git_tool_registry


class AgentExecutor:

    def __init__(self):
        self.registry = create_git_tool_registry()

    def execute(self, state: AgentState) -> AgentState:

        for task in state.tasks:

            state.current_task_id = task.id
            task.status = "running"

            try:
                tool = self.registry.get(task.id)

                tool_call = ToolCall(
                    tool_name=task.id,
                    arguments={
                        "repository_path": state.repository_path
                    },
                )

                state.tool_calls.append(tool_call)

                result = tool.execute(
                    **tool_call.arguments
                )

                tool_result = ToolResult(
                    tool_name=tool_call.tool_name,
                    success=True,
                    result=result,
                )

                state.tool_results.append(tool_result)

                task.result = result
                task.status = "completed"

                state.observations.append(
                    {
                        "tool": tool_call.tool_name,
                        "result": result,
                    }
                )

            except Exception as exc:

                tool_result = ToolResult(
                    tool_name=task.id,
                    success=False,
                    error=str(exc),
                )

                state.tool_results.append(tool_result)

                task.status = "failed"
                task.error = str(exc)

                state.observations.append(
                    {
                        "tool": task.id,
                        "error": str(exc),
                    }
                )

                state.status = "failed"

                return state

        state.status = "evaluating"

        return state