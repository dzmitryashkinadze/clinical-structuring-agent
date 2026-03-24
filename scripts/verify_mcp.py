import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def run_verification():
    """Verify MCP tools using the mcp SDK client."""
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "src/fhir_doc_tool/server.py"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            print("Verifying MCP tool: list_resources...")
            result = await session.call_tool("list_resources", {})
            print("Success! Response:")
            print(result.content[0].text)

            print("\nVerifying MCP tool: get_resource_definition(Patient)...")
            result = await session.call_tool(
                "get_resource_definition", {"resource_name": "Patient"}
            )
            print("Success! Definition starts with:")
            print(result.content[0].text[:200] + "...")


if __name__ == "__main__":
    asyncio.run(run_verification())
