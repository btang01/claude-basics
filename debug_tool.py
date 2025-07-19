import asyncio
import json
import pprint
from fastmcp import Client

async def debug_tools():
    async with Client("http://localhost:8000/mcp/") as client:
        print("Connected! Getting tools...")
        tools = await client.list_tools()

        for tool in tools:
            print(f"\n=== Tool: {tool.name} ===")
            print(f"Description: {tool.description}")
            
            # Debug the full schema structure
            print(f"\nFull inputSchema:")
            pprint.pprint(tool.inputSchema)
            
            # Check if it's nested under different keys
            schema = tool.inputSchema
            
            # Try different possible structures
            if "properties" in schema:
                properties = schema["properties"]
                print(f"\nFound properties directly:")
                for prop_name, prop_info in properties.items():
                    print(f"  {prop_name}:")
                    pprint.pprint(prop_info, indent=4)
            
            # Sometimes the schema might be nested differently
            if "parameters" in schema:
                print(f"\nFound parameters key:")
                pprint.pprint(schema["parameters"])
            
            # Check for type definitions
            if "type" in schema:
                print(f"Schema type: {schema['type']}")

if __name__ == "__main__":
    asyncio.run(debug_tools())