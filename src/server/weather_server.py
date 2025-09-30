#!/usr/bin/env python3

import requests
from fastmcp import FastMCP
from fastmcp.utilities.logging import get_logger

# Initialize logger for server lifecycle events
logger = get_logger(__name__)


# ============= MCP SERVER INITIALIZATION =============

# Create FastMCP instance with comprehensive configuration
mcp = FastMCP(
    name="weather-mcp-server",
    instructions="You are a weather assistant",
)


@mcp.tool()
def fetch_weather_data(city: str) -> str:
    url = f"http://wttr.in/{city}?format=j1"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        current = data["current_condition"][0]
        return f"Weather in {city}: {current['weatherDesc'][0]['value']}, {current['temp_F']}°F"
    except Exception:
        return f"Could not get weather for {city}"


# ============= SERVER ENTRY POINT =============

if __name__ == "__main__":
    mcp.run()
