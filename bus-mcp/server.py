import json
from typing import Any, Dict, List, Optional
from mcp.server.fastmcp import FastMCP
import asyncio
import requests
from geopy.distance import geodesic
from dataclasses import dataclass
from dotenv import load_dotenv
import os
import time
# global variables
ONE_BUS_AWAY_BASE_URL = "https://api.pugetsound.onebusaway.org/api"
CURR_TIMESTAMP_API ="where/current-time.json"

# load environment variables
ARRIVALS_AND_DEPARTURES_API="where/arrivals-and-departures-for-stop/{stop_id}.json"
load_dotenv()

# initialize the mcp server
one_bus_away_api_key = os.getenv('ONE_BUS_AWAY_API_KEY')
mcp = FastMCP("One Bus Away MCP Server")

# location class
@dataclass
class Location:
    """Location class"""
    latitude: float
    longitude: float

# make api calls
# TODO: change to use `aiohttp`?
def make_one_bus_away_api_call(endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Make One Bus Away API call
    Args:
        endpoint (str): The endpoint to call
        params (Dict[str, Any]): The parameters to pass to the endpoint

    Returns:
        Dict[str, Any]: The response from the endpoint
    """
    if params is None:
        params = {}
        
    params["key"] = one_bus_away_api_key
    url = f"{ONE_BUS_AWAY_BASE_URL}/where/{endpoint}"
    response = requests.get(url, params=params, timeout=10)
    if response.status_code != 200:
        raise requests.HTTPError(f"Failed to make API call to {url} with status code {response.status_code}: {response.text}")
    return response.json()


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


@mcp.tool(description="Convert address to latitude/longitude coordinates")
async def geocode_address(address: str) -> Dict[str, Any]:
    """Convert an address to latitude/longitude coordinates using free OpenStreetMap Nominatim API

    Args:
        address (str): Street address to geocode

    Returns:
        Dict[str, Any]: Dict containing lat, lon, and formatted address
    """
    # use openstreetmap's nominatim API (no need for API key)
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": address,
        "format": "json",
        "limit": 1,
        "addressdetails": 1,
    }
    
    headers = {
        "User-Agent": "bus-mcp/1.0"
    }
    
    response = requests.get(url, params=params, headers=headers, timeout=10)
    if response.status_code == 200:
        data = response.json()
        if data and len(data) > 0:
            result = data[0]
            return {
                "lat": float(result['lat']),
                "lon": float(result['lon']),
                "formatted_address": result['display_name']
            }
        else:
            return {"error": "Address not found"}
    else:
        raise requests.HTTPError(f"Geocoding request failed: {response.status_code}")
    
@mcp.tool(description="Find bus stops near a given location")
async def find_stops_near_location(lat: float, lon: float, radius: int = 500) -> Dict[str, Any]:
    """Find bus stops near a given location

    Args:
        lat (float): Location latitude
        lon (float): Location longitude
        radius (int, optional): Search radius in meters. Defaults to 500.

    Returns:
        Dict[str, Any]: List of bus stops within the search radius
    """
    initial_location= Location(latitude=lat, longitude=lon)
    params = {
        "lat": lat,
        "lon": lon,
        "radius": radius
    }
    
    response = make_one_bus_away_api_call("stops-for-location.json", params)

    # get data
    stops = response.get("data", {}).get("list", [])

    # formatted_stops
    formatted_stops = [(stop["name"], Location(stop["lat"], stop["lon"])) for stop in stops]    
    
    # TODO: using geodesic distance, see if we need to modify this.
    ditance_between_stops_response = [{
        "initial_location": initial_location,
        "stop_name": name,
        "stop_location": location,
        "distance_meters": geodesic((initial_location.latitude, initial_location.longitude), (location.latitude, location.longitude)).meters
    } for name, location in formatted_stops]
    
    # response should have a name, lat, long, distance
    return ditance_between_stops_response
    
@mcp.tool(description="Get information about a bus stop")
async def get_stop_details(stop_id: str) -> Dict[str, Any]:
    """Get information about a bus stop

    Args:
        stop_id (str): OneBusAway stop ID

    Returns:
        Dict[str, Any]: Bus stop info
    """
    result = make_one_bus_away_api_call(f"stop/{stop_id}.json")
    return result

@mcp.tool(description="Get real-time arrival and departure information for a stop")
async def get_stop_arrivals(stop_id: str, minutes_ahead: int = 60) -> Dict[str, Any]:
    """Get real-time arrival and departure information for a stop
    
    Args:
        stop_id (str): OneBusAway stop ID
        minutes_ahead (int): How many minutes ahead to look (default: 60)
        
    Returns:
        Dict containing arrival/departure information
    """
    params = {
        "minutesAfter": minutes_ahead
    }
    
    result = make_one_bus_away_api_call(f"arrivals-and-departures-for-stop/{stop_id}.json", params)
    return result

@mcp.tool(description="Find bus routes operating near a location")
async def find_routes_near_location(lat: float, lon: float, radius: int = 1000) -> Dict[str, Any]:
    """Find bus routes operating near a location
    
    Args:
        lat (float): Latitude
        lon (float): Longitude
        radius (int): Search radius in meters (default: 1000)
        
    Returns:
        Dict containing list of routes
    """
    params = {
        "lat": lat,
        "lon": lon,
        "radius": radius
    }
    
    result = make_one_bus_away_api_call("routes-for-location.json", params)
    return result

@mcp.tool(description="Get detailed information about a specific route")
async def get_route_details(route_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific route
    
    Args:
        route_id (str): OneBusAway route ID
        
    Returns:
        Dict containing route details
    """
    result = make_one_bus_away_api_call(f"route/{route_id}.json")
    return result

@mcp.tool(description="Get all stops served by a specific route")
async def get_route_stops(route_id: str, include_polylines: bool = False) -> Dict[str, Any]:
    """Get all stops served by a specific route
    
    Args:
        route_id (str): OneBusAway route ID
        include_polylines (bool): Include route geometry (default: False)
        
    Returns:
        Dict containing stops on the route
    """
    params = {
        "includePolylines": str(include_polylines).lower()
    }
    
    result = make_one_bus_away_api_call(f"stops-for-route/{route_id}.json", params)
    return result

# TODO: Get reachable stops from a location
# TODO: Add tool to plan a trip between two locations
# TODO: Add tool to get agency coverage
    
@mcp.tool(description="MCP Tool to get the current time")
async def get_current_time() -> Dict[str, Any]:
    request_path = f"{ONE_BUS_AWAY_BASE_URL}/{CURR_TIMESTAMP_API}?key={one_bus_away_api_key}"
    response = requests.get(request_path)
    result = response.json()
    print(f"result: {result}")
    return result

@mcp.tool(description="MCP Tool to get the next bus stops from a provided bus stop_id in the Puget Sound, Washington Area")
async def get_next_stop(stop_id,milliseconds_since_epoch = int(time.time()*1000), minutes_ahead = 35, minutes_before = 0) ->set:
    params = {
        "minutesBefore": minutes_before,
        "minutesAfter": minutes_ahead,
        "time": milliseconds_since_epoch
    }
    result = make_one_bus_away_api_call(f"arrivals-and-departures-for-stop/{stop_id}.json", params)
    write_file_path = f"random_files/{stop_id}_arrivals_and_departures.json"
    with open(write_file_path,"w") as f:
        json.dump(result,f)
    arrivalsAndDepartures = result["data"]["entry"]["arrivalsAndDepartures"]
    next_stops = set()
    for entry in arrivalsAndDepartures:
        next_stops.add(entry["tripStatus"]["nextStop"])
    print(next_stops)
    return next_stops  

async def sample_get_next_stops(stop):
    value = ""
    if stop == "S":
        value  = ["B", "A", "D"]
    if stop == "A":
        value = ["C","F","B"]
    if stop =="B":
        value = ["E"]
    if stop == "C":
        value = ["E"]
    if stop == "D":
        value = ["E"]
    if stop == "F":
        value = ["D"]
    return value
        
async def find_path(start_stop, end_stop):
    next_to_consider = [start_stop]
    stops_to_here = {} #dict of stops to a set of all the stops that could get you to key_stop.
    visited = set()
    while next_to_consider:
        stop  = next_to_consider.pop(0)
        if stop in visited:
            continue
        print(f"curr_stop: {stop}\n")
        next_stops = await sample_get_next_stops(stop)
        for next_stop in next_stops:
            if next_stop not in stops_to_here:
                stops_to_here[next_stop] = set()
            stops_to_here[next_stop].add(stop)
            next_to_consider.append(next_stop)
        visited.add(stop)
    print(f"stops_to_here: {stops_to_here}\n")
    paths  = backtrack(stops_to_here,start_stop,end_stop)
    print(paths)
    # backtrack

def backtrack(stops_to_here: Dict, start_stop,curr_stop):
    if curr_stop ==  start_stop:
        return [curr_stop]
    paths_from_here = []
    prev_stops = stops_to_here[curr_stop]
    for prev_stop in prev_stops:
        routes__from_stop_to_here = backtrack(stops_to_here,start_stop,prev_stop)
        for route in routes__from_stop_to_here:
            full_path = route + curr_stop
            paths_from_here.append(full_path)
    return paths_from_here





# test bed
if __name__ == "__main__":
    print("I am in here")
    # asyncio.run(print_hello("This is a test"))
    # asyncio.run(get_current_time())
    asyncio.run(get_next_stop("1_75403"))
    # asyncio.run(find_path("S","E"))
    mcp.run()
    