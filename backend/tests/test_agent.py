import asyncio
import os
from langchain_core.messages import HumanMessage
from app.agents.graph import app
from app.core.config import settings

# Mock env if needed or ensure .env is loaded
from dotenv import load_dotenv
load_dotenv()

async def test_agent():
    print(f"Testing Agent with Model: {settings.OPENAI_MODEL}")
    
    # query = "What is the summary of the paper related to High Frequency Trading?"
    query = "What is 25 * 4?"
    
    print(f"\nQuery: {query}")
    print("-" * 50)
    
    initial_state = {
        "messages": [HumanMessage(content=query)],
        "is_relevant": True,
        "is_supported": True,
        "documents": [],
        "reasoning_trace": [],
        "citations": []
    }
    
    # Invoke
    # Use simple invoke for test
    final_state = await app.ainvoke(initial_state)
    
    print("\nResponse:")
    print("-" * 50)
    print(final_state["messages"][-1].content)
    
    print("\nMessage History:")
    for msg in final_state["messages"]:
        print(f"{type(msg).__name__}: {msg.content[:100]}...")

if __name__ == "__main__":
    asyncio.run(test_agent())
