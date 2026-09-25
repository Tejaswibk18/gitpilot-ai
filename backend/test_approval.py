from app.agent.state import AgentState
from app.agent.gemini_agent import GeminiAgent


REPOSITORY_PATH = (
    r"C:\Users\tejaswi.b\Desktop\code"
    r"\fastapi_api_key_auth"
)


def main():

    agent = GeminiAgent()

    state = AgentState(
        user_request=(
            "Use the test_write_tool to test "
            "the approval mechanism."
        ),
        repository_path=REPOSITORY_PATH,
    )

    print("\n========== STARTING AGENT ==========")

    state = agent.run(state)

    print("\n========== STATUS ==========")
    print(state.status)

    print("\n========== APPROVAL REQUESTS ==========")

    for approval in state.approval_requests:
        print(approval.model_dump())

    if state.status == "waiting_approval":

        print("\n========== APPROVAL ==========")
        print("Simulating user approval...")

        state = agent.resume_after_approval(
            state,
            approved=True,
        )

    print("\n========== FINAL STATUS ==========")
    print(state.status)

    print("\n========== TOOL RESULTS ==========")

    for result in state.tool_results:
        print(result.model_dump())

    print("\n========== FINAL RESPONSE ==========")
    print(state.final_response)


if __name__ == "__main__":
    main()