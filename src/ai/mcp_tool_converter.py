from typing import Dict, List, Optional
from pydantic import create_model
from langchain_core.tools import Tool
from src.model.mcp import MCPTool, MCPServerConfig

class MCPToolConverter:
    cache: Dict[str, Tool] = {}

    @classmethod
    def convert(cls, mcp_tool: MCPTool, server_name: str) -> Tool:
        if mcp_tool.name in cls.cache:
            return cls.cache[mcp_tool.name]

        schema = mcp_tool.input_schema
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        fields = {}
        for prop, details in properties.items():
            field_type = details["type"]
            if field_type == "string":
                fields[prop] = (str, ...)
            elif field_type == "number":
                fields[prop] = (float, ...)
            elif field_type == "integer":
                fields[prop] = (int, ...)
            elif field_type == "boolean":
                fields[prop] = (bool, ...)
            else:
                raise ValueError(f"Неподдерживаемый тип поля: {field_type}")

        dynamic_model = create_model(mcp_tool.name.capitalize(), **fields)
        tool_func = lambda args: f"{mcp_tool.name}({args})"
        tool = Tool(
            name=mcp_tool.name,
            description=mcp_tool.description,
            func=tool_func,
            args_schema=dynamic_model
        )
        cls.cache[mcp_tool.name] = tool
        return tool
