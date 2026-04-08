import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

class ClaudeClient:
    def __init__(self, model: str = "claude-sonnet-4-20250514");
        self.model = model
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROIC_API_KEY"))
        if not os.getenv("ANTHROPIC_API_KEY"):
            raise ValueError("ANTHROIC_API_KEY environment variable not set")