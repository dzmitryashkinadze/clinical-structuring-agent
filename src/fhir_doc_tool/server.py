import os
import json
from pathlib import Path
from mcp.server import Server
from mcp.types import Tool, TextContent

DATA_DIR = Path("data/fhir_docs")
server = Server("fhir-doc-tool")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools for FHIR documentation."""
    return [
        Tool(
            name="list_resources",
            description="AC3: List all locally indexed FHIR resources.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="get_resource_definition",
            description="AC4: Get the full StructureDefinition (JSON) for a FHIR resource.",
            inputSchema={
                "type": "object",
                "properties": {
                    "resource_name": {
                        "type": "string",
                        "description": "The name of the FHIR resource (e.g., 'Patient').",
                    }
                },
                "required": ["resource_name"],
            },
        ),
        Tool(
            name="get_field_details",
            description="AC5: Get descriptions and constraints for a specific field path (e.g., 'Observation.status').",
            inputSchema={
                "type": "object",
                "properties": {
                    "resource_name": {
                        "type": "string",
                        "description": "The name of the FHIR resource.",
                    },
                    "field_path": {
                        "type": "string",
                        "description": "The full path to the field (e.g., 'Observation.valueQuantity').",
                    },
                },
                "required": ["resource_name", "field_path"],
            },
        ),
    ]


# Separate handlers for testing purposes
async def list_resources_handler(arguments: dict) -> list[TextContent]:
    indexed = [
        f.name.replace(".profile.json", "") for f in DATA_DIR.glob("*.profile.json")
    ]
    return [
        TextContent(
            type="text",
            text="\n".join(sorted(indexed)) if indexed else "No resources indexed.",
        )
    ]


def minify_fhir_schema(definition: dict) -> list[dict]:
    """Phase 1.5 AC1-AC3: Reduce StructureDefinition to bare minimum for LLM context."""
    snapshot_elements = definition.get("snapshot", {}).get("element", [])
    minified = []

    for element in snapshot_elements:
        path = element.get("path", "")

        # Filter out extensions and base IDs
        if (
            path.endswith(".extension")
            or path.endswith(".modifierExtension")
            or (path.endswith(".id") and path != definition.get("name"))
        ):
            continue

        clean_element = {"path": path}

        # Keep only the essentials
        if "short" in element:
            clean_element["short"] = element["short"]
        if "min" in element:
            clean_element["min"] = element["min"]
        if "max" in element:
            clean_element["max"] = element["max"]
        if "type" in element:
            clean_element["type"] = [
                t.get("code") for t in element["type"] if "code" in t
            ]
        if "binding" in element:
            # Provide binding details if they exist to guide the LLM on what codes to use
            binding = element["binding"]
            clean_element["binding"] = {
                "strength": binding.get("strength"),
                "description": binding.get("description"),
                "valueSet": binding.get("valueSet"),
            }

        minified.append(clean_element)

    return minified


async def get_definition_handler(arguments: dict) -> list[TextContent]:
    res = arguments.get("resource_name")
    path = DATA_DIR / f"{res}.profile.json"
    if not path.exists():
        return [TextContent(type="text", text=f"Resource '{res}' not indexed.")]
    with open(path) as f:
        definition = json.load(f)
        minified = minify_fhir_schema(definition)
        return [TextContent(type="text", text=json.dumps(minified, indent=2))]


async def get_field_details_handler(arguments: dict) -> list[TextContent]:
    res = arguments.get("resource_name")
    path = arguments.get("field_path")
    profile_path = DATA_DIR / f"{res}.profile.json"
    if not profile_path.exists():
        return [TextContent(type="text", text=f"Resource '{res}' not indexed.")]
    with open(profile_path) as f:
        definition = json.load(f)
        snapshot = definition.get("snapshot", {}).get("element", [])
        element = next((e for e in snapshot if e.get("path") == path), None)
        if element:
            return [TextContent(type="text", text=json.dumps(element, indent=2))]
        else:
            return [
                TextContent(
                    type="text", text=f"Field '{path}' not found in resource '{res}'."
                )
            ]


@server.call_tool()
async def call_tool_handler(name: str, arguments: dict) -> list[TextContent]:
    """Handle MCP tool calls."""
    if name == "list_resources":
        return await list_resources_handler(arguments)
    elif name == "get_resource_definition":
        return await get_definition_handler(arguments)
    elif name == "get_field_details":
        return await get_field_details_handler(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")


if __name__ == "__main__":
    from mcp.server.stdio import stdio_server
    import asyncio

    async def main():
        async with stdio_server() as (read, write):
            await server.run(read, write, server.create_initialization_options())

    asyncio.run(main())
