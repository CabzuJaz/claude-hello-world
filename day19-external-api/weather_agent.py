import anthropic
import os
import requests
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
WEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

# ─────────────────────────────────────────
# TOOLS
# ─────────────────────────────────────────

tools = [
    {
        "name": "get_current_weather",
        "description": "Get real-time weather data for any city using OpenWeatherMap.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City name e.g. Manila, Tokyo, London"
                },
                "units": {
                    "type": "string",
                    "enum": ["metric", "imperial"],
                    "default": "metric",
                    "description": "metric = Celsius, imperial = Fahrenheit"
                }
            },
            "required": ["city"]
        }
    },
    {
        "name": "get_forecast",
        "description": "Get 5-day weather forecast for a city.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {"type": "string"},
                "units": {
                    "type": "string",
                    "enum": ["metric", "imperial"],
                    "default": "metric"
                }
            },
            "required": ["city"]
        }
    }
]

# ─────────────────────────────────────────
# REAL API CALLS
# ─────────────────────────────────────────

def get_current_weather(city: str, units: str = "metric") -> str:
    print(f"  [get_current_weather] Fetching: '{city}'")
    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": city,
            "appid": WEATHER_API_KEY,
            "units": units
        }
        response = requests.get(url, params=params)
        data = response.json()

        if response.status_code != 200:
            return f"Error: {data.get('message', 'Unknown error')}"

        unit_symbol = "°C" if units == "metric" else "°F"
        return (
            f"City: {data['name']}, {data['sys']['country']}\n"
            f"Temperature: {data['main']['temp']}{unit_symbol} "
            f"(feels like {data['main']['feels_like']}{unit_symbol})\n"
            f"Condition: {data['weather'][0]['description'].title()}\n"
            f"Humidity: {data['main']['humidity']}%\n"
            f"Wind: {data['wind']['speed']} m/s"
        )
    except Exception as e:
        return f"Weather API error: {e}"

def get_forecast(city: str, units: str = "metric") -> str:
    print(f"  [get_forecast] Fetching forecast: '{city}'")
    try:
        url = "https://api.openweathermap.org/data/2.5/forecast"
        params = {
            "q": city,
            "appid": WEATHER_API_KEY,
            "units": units,
            "cnt": 5
        }
        response = requests.get(url, params=params)
        data = response.json()

        if response.status_code != 200:
            return f"Error: {data.get('message', 'Unknown error')}"

        unit_symbol = "°C" if units == "metric" else "°F"
        forecasts = []
        for item in data["list"]:
            forecasts.append(
                f"{item['dt_txt']}: "
                f"{item['main']['temp']}{unit_symbol}, "
                f"{item['weather'][0]['description']}"
            )
        return "\n".join(forecasts)
    except Exception as e:
        return f"Forecast API error: {e}"

def run_tool(name: str, tool_input: dict) -> str:
    if name == "get_current_weather":
        return get_current_weather(
            tool_input["city"],
            tool_input.get("units", "metric")
        )
    elif name == "get_forecast":
        return get_forecast(
            tool_input["city"],
            tool_input.get("units", "metric")
        )
    return f"Unknown tool: {name}"

# ─────────────────────────────────────────
# AGENT LOOP
# ─────────────────────────────────────────

def run_agent(user_message: str):
    print(f"\n{'='*50}")
    print(f"User: {user_message}")
    print(f"{'='*50}")

    messages = [{"role": "user", "content": user_message}]

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1024,
            system="You are a helpful weather assistant. Use the tools to get real weather data before answering. Always give practical advice based on the weather.",
            tools=tools,
            messages=messages
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    print(f"\nClaude: {block.text}")
            break
        elif response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"  → Calling: {block.name}({block.input})")
                    result = run_tool(block.name, block.input)
                    print(f"  ← {result[:100]}...")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(result)
                    })
            messages.append({"role": "user", "content": tool_results})
        else:
            print(f"Unexpected stop_reason: {response.stop_reason}")
            break

if __name__ == "__main__":
    # Test 1 — single city
    run_agent("What's the weather like in Manila right now? Should I bring an umbrella?")

    # Test 2 — compare two cities
    run_agent("Compare the weather in Manila and Tokyo. Which is better for outdoor activities today?")

    # Test 3 — forecast
    run_agent("What's the forecast for Cavite, Philippines for the next few days?")