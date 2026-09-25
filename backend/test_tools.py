from app.agent.git_tools import create_git_tool_registry

def main():
    registry = create_git_tool_registry()

    print("\n========== REGISTERED TOOLS ==========")

    for tool in registry.list_tools():
        print(f"\nTool: {tool.name}")
        print(f"Description: {tool.description}")
        print(f"Risk: {tool.risk}")
        print(f"Requires approval: {tool.requires_approval}")

        print("Parameters:")

        for parameter in tool.parameters:
            print(
                f"  - {parameter.name}: "
                f"{parameter.type} "
                f"(required={parameter.required})"
            )

    print("\n========== LLM TOOL SCHEMAS ==========")

    for schema in registry.get_schemas():
        print(schema)


if __name__ == "__main__":
    main()