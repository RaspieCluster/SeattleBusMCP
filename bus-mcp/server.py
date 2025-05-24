from typing import Any, Dict
from mcp.server.fastmcp import FastMCP
import asyncio
import requests

from dotenv import load_dotenv
import os
ONE_BUS_AWAY_BASE_URL = "https://api.pugetsound.onebusaway.org/api"
CURR_TIMESTAMP_API ="where/current-time.json"
load_dotenv()
one_bus_away_api_key = os.getenv('ONE_BUS_AWAY_API_KEY')
mcp = FastMCP("One Bus Away MCP Server")

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

@mcp.tool(description="MCP Tool to get the current time")
async def get_current_time() -> Dict[str, Any]:
    
    request_path = f"{ONE_BUS_AWAY_BASE_URL}/{CURR_TIMESTAMP_API}?key={one_bus_away_api_key}"
    response = requests.get(request_path)
    result = response.json()
    print(f"result: {result}")
    return result
    

# test bed
if __name__ == "__main__":
    print("I am in here")
    asyncio.run(print_hello("This is a test"))
    asyncio.run(get_current_time())
    mcp.run()