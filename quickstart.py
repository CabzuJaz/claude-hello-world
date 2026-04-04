from dotenv import load_dotenv
import os

load_dotenv()  # this must run before you create the client

import anthropic

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

message = client.messages.create(
	model="claude-sonnet-4-20250514",
	max_tokens=1000,
	messages=[
		{
            "role": "user",
            "content": "What is the meaning of life?"
		}
	],
)
print(message.content)