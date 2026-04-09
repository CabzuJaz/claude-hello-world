import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

class ClaudeClient:
    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        self.model = model
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROIC_API_KEY"))
        if not os.getenv("ANTHROPIC_API_KEY"):
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
    def ask (self, prompt: str, max_tokens: int = 1024) -> str:
        message = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    
    def ask_with_system(self, prompt: str, system: str, max_tokens: int = 1024) -> str:
        message = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role":"user", "content": prompt}]
        )
        return message.content[0].text
        
if __name__ == "__main__":
    claude = ClaudeClient()

    print("=== Basic Ask ===")
    print(claude.ask("Explain what an API is in 2 sentences."))

    print("\n=== With System Prompt ===")
    print(claude.ask_with_system(
        prompt="What is gravity?",
        system="You are explaining to a 5-year-old. Use simple words and one short analogy."
    ))