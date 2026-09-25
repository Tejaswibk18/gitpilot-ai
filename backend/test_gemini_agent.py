from app.agent.state import AgentState
from app.agent.gemini_agent import GeminiAgent


REPOSITORY_PATH = (
    r"C:\Users\tejaswi.b\Desktop\code"
    r"\fastapi_api_key_auth"
)


def main():

    state = AgentState(
        user_request="Show me my current changes",
        repository_path=REPOSITORY_PATH,
    )

    agent = GeminiAgent()

    state = agent.run(state)

    print("\n========== STATUS ==========")
    print(state.status)

    print("\n========== TOOL CALLS ==========")

    for tool_call in state.tool_calls:
        print(tool_call.model_dump())

    print("\n========== TOOL RESULTS ==========")

    for result in state.tool_results:
        print(result.model_dump())

    print("\n========== FINAL RESPONSE ==========")
    print(state.final_response)


if __name__ == "__main__":
    main()