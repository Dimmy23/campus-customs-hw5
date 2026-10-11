from __future__ import annotations

from pathlib import Path
from typing import Any

from fastmcp import Client


SERVER_PATH = Path(__file__).resolve().parents[1] / "mcp_server" / "mcp_server.py"


async def call_mcp(tool_name: str, arguments: dict[str, Any]) -> Any:
    """Call the Campus Customs MCP server; no direct database access is allowed here."""
    async with Client(SERVER_PATH) as client:
        result = await client.call_tool(tool_name, arguments)
        if hasattr(result, "data") and result.data is not None:
            return result.data
        if hasattr(result, "content"):
            return [item.text for item in result.content if getattr(item, "text", None)]
        return result
