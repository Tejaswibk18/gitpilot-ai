from app.agent.agent import GitPilotAgent


REPOSITORY_PATH = (
    r"C:\Users\tejaswi.b\Desktop\code"
    r"\fastapi_api_key_auth"
)


def main():

    agent = GitPilotAgent()

    state = agent.run(
        user_request="Show me my current changes",
        repository_path=REPOSITORY_PATH,
    )

    print("\n========== AGENT STATUS ==========")
    print(state.status)

    print("\n========== TOOL CALLS ==========")

    for tool_call in state.tool_calls:
        print(tool_call.model_dump())

    print("\n========== TOOL RESULTS ==========")

    for result in state.tool_results:
        print({
            "tool": result.tool_name,
            "success": result.success,
        })

    print("\n========== FINAL RESPONSE ==========")
    print(state.final_response)


if __name__ == "__main__":
    main()