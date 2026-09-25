from app.agent.state import AgentState
from app.agent.gemini_agent import GeminiAgent


class GitPilotAgent:

    def __init__(self):
        self.gemini_agent = GeminiAgent()

    def run(
        self,
        user_request: str,
        repository_path: str,
    ) -> AgentState:

        state = AgentState(
            user_request=user_request,
            repository_path=repository_path,
            status="planning",
        )

        return self.gemini_agent.run(state)