import anthropic

client = anthropic.Anthropic()

def researcher_agent(topic: str) -> str:
    """Subagent 1: Researches a topic and returns raw facts."""
    print(f"[Researcher] Researching: {topic}")
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        system="You are a research specialist. Return only bullet-point facts. Be concise.",
        messages=[{"role": "user", "content": f"Give me 5 key facts about: {topic}"}]
    )
    return response.content[0].text

def writer_agent(topic: str, facts: str) -> str:
    """Subagent 2: Turns raw facts into a polished paragraph."""
    print(f"[Writer] Writing about: {topic}")
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        system="You are a professional writer. Turn bullet points into one clear, engaging paragraph.",
        messages=[{
            "role": "user",
            "content": f"Topic: {topic}\n\nFacts:\n{facts}\n\nWrite a polished paragraph."
        }]
    )
    return response.content[0].text

def orchestrator(user_request: str) -> str:
    """Orchestrator: Breaks the task, delegates to subagents, combines results."""
    print(f"\n[Orchestrator] Received: {user_request}")
    
    # Step 1: Ask orchestrator to identify the topic
    plan_response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=100,
        system="You extract the core topic from a user request. Reply with only the topic, nothing else.",
        messages=[{"role": "user", "content": user_request}]
    )
    topic = plan_response.content[0].text.strip()
    print(f"[Orchestrator] Extracted topic: {topic}")

    # Step 2: Delegate to Researcher
    facts = researcher_agent(topic)
    print(f"[Researcher] Done.\n{facts}\n")

    # Step 3: Delegate to Writer
    article = writer_agent(topic, facts)
    print(f"[Writer] Done.\n{article}\n")

    # Step 4: Orchestrator delivers final result
    print("[Orchestrator] Pipeline complete.")
    return article

if __name__ == "__main__":
    result = orchestrator("Tell me about the Python programming language")
    print("\n===== FINAL OUTPUT =====")
    print(result)