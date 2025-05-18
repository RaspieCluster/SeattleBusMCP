from mcp.server.fastmcp import FastMCP
import asyncio

mcp = FastMCP("Azure Data Explorer MCP")

@mcp.tool(description="MCP Tool to print hello world")
async def print_hello(input_name: str) -> str:
    """Small MCP Tool

    Args:
        input_name (str): String to print out

    Returns:
        str: Greeting message
    """
    print(f"Hello {input_name}!")
    print("Hello, world!")
    return f"Hello {input_name}!"

# test bed
if __name__ == "__main__":
    print("I am in here")
    asyncio.run(print_hello("This is a test"))
    mcp.run()