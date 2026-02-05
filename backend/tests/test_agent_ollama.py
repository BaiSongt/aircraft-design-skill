import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.services.ai_service import global_ai_manager
from backend.agents.design_agent import DesignAgent

async def test_ollama_agent():
    print("Testing Ollama + Design Agent (Streaming)...")
    
    # 1. Get Ollama Provider
    try:
        # Update config for local testing to use 127.0.0.1 explicitly
        ollama_config = global_ai_manager.get_provider_config("ollama")
        if ollama_config:
            ollama_config['baseUrl'] = "http://127.0.0.1:11434/v1"
            global_ai_manager.add_provider("ollama", ollama_config)
            if "ollama" in global_ai_manager.providers:
                del global_ai_manager.providers["ollama"]

        provider = global_ai_manager.get_provider("ollama")
        print(f"Successfully got provider: {provider}")
              
    except Exception as e:
        print(f"Error getting provider: {e}")
        return

    # 2. Initialize Agent
    agent = DesignAgent(llm=provider)
    print("Agent initialized.")

    # 3. Test Query (Requires Tool Use)
    query = "Calculate the standard atmosphere properties at 10000 meters altitude."
    print(f"Sending query: {query}")
    print("-" * 50)
    
    try:
        async for event in agent.astream(query):
            kind = event["event"]
            if kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if hasattr(chunk, "content") and chunk.content:
                    print(chunk.content, end="", flush=True)
            elif kind == "on_tool_start":
                print(f"\n[TOOL START: {event['name']}] Input: {event['data'].get('input')}")
            elif kind == "on_tool_end":
                print(f"\n[TOOL END: {event['name']}] Output: {str(event['data'].get('output'))[:100]}...")
        
        print("\n" + "-" * 50)
        print("Streaming complete.")

    except Exception as e:
        print(f"\nError executing agent: {e}")

if __name__ == "__main__":
    # Ensure no_proxy is set for localhost
    os.environ["no_proxy"] = "localhost,127.0.0.1"
    asyncio.run(test_ollama_agent())
