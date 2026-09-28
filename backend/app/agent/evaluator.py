from app.agent.state import AgentState

class AgentEvaluator:
    def evaluate(self, state: AgentState) -> AgentState:
        failed_tasks = [
            task for task in state.tasks
            if task.status == "failed"
        ]

        if failed_tasks:
            state.status = "failed"
            state.final_response = (
                "The agent could not complete the requested operation."
            )
            return state

        state.status = "completed"
        state.final_response = (
            "The requested repository information has been collected successfully."
        )

        return state