from google.genai import types

from app.agent.git_tools import create_git_tool_registry
from app.agent.state import (
    AgentState,
    ToolCall,
    ToolResult,
)
from app.agent.approval import ApprovalManager
from app.services.llm_service import LLMService


class GeminiAgent:

    def __init__(self):
        self.llm = LLMService()
        self.registry = create_git_tool_registry()
        self.approval_manager = ApprovalManager()

    def run(self, state: AgentState) -> AgentState:

        tool_declarations = self.registry.get_gemini_schemas()

        system_instruction = """
You are GitPilot AI, an agent that helps users operate
Git repositories safely.

You have access to Git tools.

Rules:

1. Use tools when repository information is required.
2. Never invent a tool.
3. Use the minimum number of tools necessary.
4. Inspect repository state before performing changes.
5. Never bypass the application's approval system.
6. Write and destructive operations require approval.
7. After receiving a tool result, decide whether another
   tool is required or whether you can answer the user.
8. Give a concise final response summarizing what happened.
"""

        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part(
                        text=(
                            f"Repository path:\n"
                            f"{state.repository_path}\n\n"
                            f"User request:\n"
                            f"{state.user_request}"
                        )
                    )
                ],
            )
        ]

        config = self._create_config(
            tool_declarations,
            system_instruction,
        )

        response = self.llm.client.models.generate_content(
            model=self.llm.model,
            contents=contents,
            config=config,
        )

        return self._process_response(
            state=state,
            response=response,
            contents=contents,
            config=config,
        )

    # --------------------------------------------------
    # RESPONSE PROCESSING
    # --------------------------------------------------

    def _process_response(
        self,
        state: AgentState,
        response,
        contents,
        config,
    ) -> AgentState:

        function_calls = response.function_calls

        # --------------------------------------------------
        # GEMINI RETURNED A FINAL TEXT RESPONSE
        # --------------------------------------------------

        if not function_calls:

            state.final_response = response.text
            state.status = "completed"

            return state

        # --------------------------------------------------
        # PRESERVE GEMINI'S FUNCTION CALL MESSAGE
        # --------------------------------------------------

        contents.append(
            response.candidates[0].content
        )

        # --------------------------------------------------
        # PROCESS TOOL CALLS
        # --------------------------------------------------

        for function_call in function_calls:

            tool_name = function_call.name

            arguments = dict(
                function_call.args
            )

            tool_call = ToolCall(
                tool_name=tool_name,
                arguments=arguments,
            )

            state.tool_calls.append(
                tool_call
            )

            tool = self.registry.get(
                tool_name
            )

            # --------------------------------------------------
            # APPROVAL REQUIRED
            # --------------------------------------------------

            if tool.requires_approval:

                approval = (
                    self.approval_manager.create_request(
                        tool_name=tool_name,
                        arguments=arguments,
                        risk=tool.risk,
                    )
                )

                state.approval_requests.append(
                    approval
                )

                state.pending_tool_call = (
                    tool_call
                )

                state.status = (
                    "waiting_approval"
                )

                state.final_response = (
                    f"Approval required to execute "
                    f"'{tool_name}'."
                )

                return state

            # --------------------------------------------------
            # EXECUTE READ-ONLY TOOL
            # --------------------------------------------------

            result = self._execute_tool(
                state=state,
                tool_name=tool_name,
                arguments=arguments,
            )

            # --------------------------------------------------
            # SEND TOOL RESULT BACK TO GEMINI
            # --------------------------------------------------

            contents.append(
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_function_response(
                            name=tool_name,
                            response={
                                "result": result
                            },
                        )
                    ],
                )
            )

        # --------------------------------------------------
        # ASK GEMINI WHAT TO DO NEXT
        # --------------------------------------------------

        next_response = (
            self.llm.client.models.generate_content(
                model=self.llm.model,
                contents=contents,
                config=config,
            )
        )

        return self._process_response(
            state=state,
            response=next_response,
            contents=contents,
            config=config,
        )

    # --------------------------------------------------
    # APPROVAL RESUME
    # --------------------------------------------------

    def resume_after_approval(
        self,
        state: AgentState,
        approved: bool,
    ) -> AgentState:

        if state.status != "waiting_approval":
            raise ValueError(
                "Agent is not waiting for approval."
            )

        if state.pending_tool_call is None:
            raise ValueError(
                "No pending tool call exists."
            )

        tool_call = state.pending_tool_call

        # --------------------------------------------------
        # FIND PENDING APPROVAL
        # --------------------------------------------------

        approval = next(
            (
                item
                for item in state.approval_requests
                if (
                    item.tool_name
                    == tool_call.tool_name
                    and item.status == "pending"
                )
            ),
            None,
        )

        if approval is None:
            raise ValueError(
                "No pending approval request exists."
            )

        # --------------------------------------------------
        # USER REJECTED
        # --------------------------------------------------

        if not approved:

            self.approval_manager.reject(
                approval
            )

            state.status = "rejected"

            state.final_response = (
                f"Execution of "
                f"'{tool_call.tool_name}' "
                "was rejected by the user."
            )

            state.pending_tool_call = None

            return state

        # --------------------------------------------------
        # USER APPROVED
        # --------------------------------------------------

        self.approval_manager.approve(
            approval
        )

        tool = self.registry.get(
            tool_call.tool_name
        )

        try:

            result = tool.execute(
                **tool_call.arguments
            )

            state.tool_results.append(
                ToolResult(
                    tool_name=tool_call.tool_name,
                    success=True,
                    result=result,
                )
            )

            state.observations.append(
                {
                    "tool": tool_call.tool_name,
                    "result": result,
                }
            )

        except Exception as exc:

            state.tool_results.append(
                ToolResult(
                    tool_name=tool_call.tool_name,
                    success=False,
                    error=str(exc),
                )
            )

            state.pending_tool_call = None

            state.status = "failed"

            state.final_response = (
                f"Tool '{tool_call.tool_name}' "
                f"failed: {exc}"
            )

            return state

        # --------------------------------------------------
        # APPROVED TOOL EXECUTED
        # --------------------------------------------------

        state.pending_tool_call = None

        state.status = "completed"

        state.final_response = (
            f"Approved tool "
            f"'{tool_call.tool_name}' "
            "was executed successfully."
        )

        return state

    # --------------------------------------------------
    # TOOL EXECUTION
    # --------------------------------------------------

    def _execute_tool(
        self,
        state: AgentState,
        tool_name: str,
        arguments: dict,
    ):

        tool = self.registry.get(
            tool_name
        )

        result = tool.execute(
            **arguments
        )

        state.tool_results.append(
            ToolResult(
                tool_name=tool_name,
                success=True,
                result=result,
            )
        )

        state.observations.append(
            {
                "tool": tool_name,
                "result": result,
            }
        )

        return result

    # --------------------------------------------------
    # GEMINI CONFIGURATION
    # --------------------------------------------------

    def _create_config(
        self,
        tool_declarations,
        system_instruction,
    ):

        return types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=[
                types.Tool(
                    function_declarations=(
                        tool_declarations
                    )
                )
            ],
            automatic_function_calling=(
                types.AutomaticFunctionCallingConfig(
                    disable=True
                )
            ),
        )