from typing import Callable, Any, Literal
from pydantic import BaseModel


ToolRisk = Literal["read", "write", "destructive"]


class ToolParameter(BaseModel):
    name: str
    type: str
    description: str
    required: bool = True


class Tool:
    def __init__(
        self,
        name: str,
        description: str,
        function: Callable[..., Any],
        parameters: list[ToolParameter] | None = None,
        risk: ToolRisk = "read",
        requires_approval: bool = False,
    ):
        self.name = name
        self.description = description
        self.function = function
        self.parameters = parameters or []
        self.risk = risk
        self.requires_approval = requires_approval

    def execute(self, **kwargs):
        expected_parameters = {
            parameter.name
            for parameter in self.parameters
        }

        unknown_parameters = set(kwargs) - expected_parameters

        if unknown_parameters:
            raise ValueError(
                f"Unknown parameters for tool '{self.name}': "
                f"{unknown_parameters}"
            )

        missing_parameters = {
            parameter.name
            for parameter in self.parameters
            if parameter.required and parameter.name not in kwargs
        }

        if missing_parameters:
            raise ValueError(
                f"Missing parameters for tool '{self.name}': "
                f"{missing_parameters}"
            )

        return self.function(**kwargs)

    def schema(self) -> dict:
        properties = {}

        for parameter in self.parameters:
            properties[parameter.name] = {
                "type": parameter.type,
                "description": parameter.description,
            }

        required = [
            parameter.name
            for parameter in self.parameters
            if parameter.required
        ]

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }

    def gemini_schema(self) -> dict:
        properties = {}

        for parameter in self.parameters:
            properties[parameter.name] = {
                "type": parameter.type.upper(),
                "description": parameter.description,
            }

        required = [
            parameter.name
            for parameter in self.parameters
            if parameter.required
        ]

        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "OBJECT",
                "properties": properties,
                "required": required,
            },
        }


class ToolRegistry:
    def __init__(self):
        self.tools: dict[str, Tool] = {}

    def register(self, tool: Tool):
        self.tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        if name not in self.tools:
            raise ValueError(f"Tool not found: {name}")

        return self.tools[name]

    def list_tools(self) -> list[Tool]:
        return list(self.tools.values())

    def get_schemas(self) -> list[dict]:
        return [
            tool.schema()
            for tool in self.tools.values()
        ]

    def get_gemini_schemas(self) -> list[dict]:
        return [
            tool.gemini_schema()
            for tool in self.tools.values()
        ]