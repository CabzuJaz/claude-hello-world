import anthropic
import os
import json
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

import time

def call_with_retry(func, *args, max_retries=3, **kwargs):
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except anthropic.APIStatusError as e:
            if e.status_code == 529:
                wait = (attempt + 1) * 5  # 5s, 10s, 15s
                print(f"Server overloaded. Retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise
    raise RuntimeError("Max retries reached. Try again later.")

# --- Step 1: Define your tools (what Claude can call) ---
tools = [
    {
        "name": "get_weather",
        "description": "Get the current weather for a city",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "The city name, e.g Manila"
                }
            },
            "required": ["city"]
        }
    }
]
# --- Step 2: Your actual python function (mock data for now) ---
def get_weather(city:str) -> str:
    mock_data = {
        "manila": "32°C, humid, partly cloudy",
        "tokyo": "18°C, clear skies",
        "london": "12°C, rainy"
    }
    return mock_data.get(city.lower(), f"No weather data for {city}")

# --- Step 3: The tool use loop ---
def run_with_tools(user_message:str):
    print(f"\nUser: {user_message}") 
    
    
    # First API call - Claude decide if it needs to use a tool
    response = call_with_retry(
        client.messages.create,
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        tools=tools,
        messages=[{"role": "user", "content": user_message}]
    )

    # First API call - Claude decide if it needs to use a tool
#    response = client.messages.create(
#        model="claude-sonnet-4-20250514",
#        max_tokens = 1024,
#        tools=tools,
#        messages=[{"role": "user", "content": user_message}]
#   )

    print(f"Stop reason: {response.stop_reason}")

    # If claude wants to use a tool
    if response.stop_reason == "tool_use":
        # Find the tool call in the response
        tool_use_block = next(b for b in response.content if b.type == "tool_use")
        tool_name = tool_use_block.name
        tool_input = tool_use_block.input

        print(f"Claude wants to call: {tool_name} {tool_input}")

        # Actually run your function
        if tool_name == "get_weather":
            result = get_weather(tool_input["city"])

        print(f"Tool result: {result}")

        # Second API call - send the result back to Claude
        final_response = client.messages.create(
            model = "claude-sonnet-4-20250514",
            max_tokens = 1024,
            tools = tools,
            messages=[
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": response.content},
                {
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": tool_use_block.id,
                        "content": result
                    }]
                }
            ]
        )

        print(f"\nClaude: {final_response.content[0].text}")

    else:
        # Claude answered directly withoout needing a tool
        print(f"\nClaude: {response.content[0].text}")

# --- Test ---
run_with_tools("What's the weather like in Manila?")
run_with_tools("What's the weather like in Tokyo?")
run_with_tools("What is 2+2?") #This one won't use the tool