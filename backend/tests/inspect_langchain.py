import langchain
import langchain.agents
print(f"LangChain version: {langchain.__version__}")
print(f"Agents dir: {dir(langchain.agents)}")
try:
    from langchain.agents import AgentExecutor
    print("AgentExecutor found in agents")
except ImportError:
    print("AgentExecutor NOT found in agents")

try:
    from langchain.agents.agent import AgentExecutor
    print("AgentExecutor found in agents.agent")
except ImportError:
    print("AgentExecutor NOT found in agents.agent")
