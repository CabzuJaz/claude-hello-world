import anthropic
import os
import json
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

MEMORY_FILE = "memory.json"

# --- Load conversation history from file ---"
def load_memory() -> list:
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return []

# --- Save conversation history to file ---"
def save_memory(memory: list) -> None:
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)

# --- Chat with memory ---"
def chat(user_input: str, history: list) -> str:
    # Add user input to history
    history.append({"role": "user", "content": user_input})
    
    # Get response from Claude
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system = "You are a helpful assistant with a great memory. Always refer back to what the user told you earlier in the conversation when relevant.",
        messages=history       
    )

    assistant_message = response.content[0].text
    history.append({"role": "assistant", "content": assistant_message})
    save_memory(history)
    return assistant_message


# --- Main loop ---"
def Main():
    history = load_memory()

    if history:
        print(f"Loaded {len(history)} messages from memory. \n")
    else:
        print("Starting fresh conversation. \n")
    
    print("Type 'quit' to exit, 'clear' to reset memory. \n")

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() == "quit":
            print("Goodbye! Conversation saved.")
            break
        elif user_input.lower() == "clear":
            history = []
            save_memory (history)
            print("Memory cleared. Starting fresh. \n")
            continue
        elif not user_input:
            continue

        response = chat(user_input, history)
        print(f"\nClaude: {response}\n")


if __name__ == "__main__":    Main()

