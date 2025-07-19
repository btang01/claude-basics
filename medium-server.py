from fastmcp import FastMCP

mcp = FastMCP("MyMCPServer")

@mcp.tool
async def web_search(query: str) -> str:
    """Simulate a web search of running a query against search api and returning answer"""

    return (
        "1. The Verge: Sam Altman is the current CEO of OpenAI.\n"
        "2. TechCrunch: OpenAI's leadership team is led by Sam Altman, who returned in 2023.\n"
        "3. Bloomberg: Former Y Combinator president Sam Altman is CEO of OpenAI.\n"
    )

@mcp.tool
async def read_file(path: str) -> str:
    """read the contents of a file given a specified file path"""
    try:
        with open(path, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return f"ERROR: file not found: {path}"
    except Exception as e:
        return f"ERROR: could not read file {path}: {str(e)}"
    
@mcp.tool
async def write_file(path: str, content: str) -> str:
    """Write given content to a file, given a specified file path"""
    try:
        with open(path, "w") as f:
            f.write(content.strip() + "\n")
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"ERROR: unable to write to file {path}: {str(e)}"

if __name__ == "__main__":
    print("Starting MCP server on http://localhost:8000")
    mcp.run(transport="http", host="localhost", port="8000")