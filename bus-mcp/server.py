import json
from typing import Any, Dict
from mcp.server.fastmcp import FastMCP
import asyncio
import requests

from dotenv import load_dotenv
import os
ONE_BUS_AWAY_BASE_URL = "https://api.pugetsound.onebusaway.org/api"
CURR_TIMESTAMP_API ="where/current-time.json"
ARRIVALS_AND_DEPARTURES_API="where/arrivals-and-departures-for-stop/{stop_id}.json"
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

@mcp.tool(description="MCP Tool to get the next bus stops from a provided bus stop_id in the Puget Sound, Washington Area")
async def get_next_stop(stop_id) ->set:
    request_path = f"{ONE_BUS_AWAY_BASE_URL}/{ARRIVALS_AND_DEPARTURES_API}?key={one_bus_away_api_key}".replace("{stop_id}",stop_id)
    response = requests.get(request_path)
    result = response.json()
    write_file_path = f"{stop_id}_arrivals_and_departures.json"
    with open(write_file_path,"w") as f:
        json.dump(result,f)
    arrivalsAndDepartures = result["data"]["entry"]["arrivalsAndDepartures"]
    next_stops = set()
    for entry in arrivalsAndDepartures:
        next_stops.add(entry["tripStatus"]["nextStop"])
    print(next_stops)
    return next_stops  

# test bed
if __name__ == "__main__":
    print("I am in here")
    asyncio.run(print_hello("This is a test"))
    asyncio.run(get_current_time())
    asyncio.run(get_next_stop("1_75403"))
    mcp.run()