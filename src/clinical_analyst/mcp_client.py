from typing import List, Dict, Any
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from .config import settings


class FHIRDocClient:
    """Bridge to the FHIR Doc Tool MCP Server."""

    def __init__(
        self,
        command: str = settings.MCP_SERVER_COMMAND,
        args: str = settings.MCP_SERVER_ARGS,
    ):
        self.server_params = StdioServerParameters(
            command=command, args=args.split(",")
        )

    async def list_resources(self) -> List[str]:
        """AC3: List all locally indexed FHIR resources."""
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("list_resources", {})
                resources = result.content[0].text.split("\n")
                return [r for r in resources if r and r != "No resources indexed."]

    async def get_resource_definition(self, resource_name: str) -> Dict[str, Any]:
        """AC4: Get the full StructureDefinition for a FHIR resource."""
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "get_resource_definition", {"resource_name": resource_name}
                )
                if "not indexed" in result.content[0].text:
                    raise ValueError(result.content[0].text)
                import json

                return json.loads(result.content[0].text)  # type: ignore[no-any-return]

    async def get_field_details(
        self, resource_name: str, field_path: str
    ) -> Dict[str, Any]:
        """AC5: Get descriptions and constraints for a specific field path."""
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "get_field_details",
                    {"resource_name": resource_name, "field_path": field_path},
                )
                import json

                return json.loads(result.content[0].text)  # type: ignore[no-any-return]
