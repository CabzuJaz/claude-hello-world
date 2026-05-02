from mcp.server.fastmcp import FastMCP
from ddgs import DDGS

# Create the MCP server
mcp = FastMCP("research-tools")

@mcp.tool()
def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    # Fake weather data — same as Day 3
    weather_data = {
        "Manila": "32°C, humid, partly cloudy",
        "Tokyo": "18°C, clear skies",
        "London": "12°C, overcast",
        "New York": "22°C, sunny",
    }
    return weather_data.get(city, f"Weather data not available for {city}")

@mcp.tool()
def search_web(query: str, max_results: int = 5) -> str:
    """Search the web for information on a given topic."""
    print(f"[search_web] Searching: '{query}'")
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        if not results:
            return "No results found."
        formatted = []
        for i, r in enumerate(results, 1):
            formatted.append(f"{i}. {r['title']} - {r['body']}")
        return "\n\n".join(formatted)
    except Exception as e:
        return f"Search error: {e}"

if __name__ == "__main__":
    mcp.run()