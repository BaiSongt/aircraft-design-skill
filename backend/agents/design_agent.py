from typing import List, Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate

from backend.tools.atmosphere_tool import calculate_atmosphere
from backend.tools.aerodynamics_tool import calculate_lift_slope

class DesignAgent:
    def __init__(self, llm: BaseChatModel, tools: Optional[List[BaseTool]] = None):
        self.llm = llm
        self.tools = tools or [calculate_atmosphere, calculate_lift_slope]
        self.agent_executor = self._create_agent()

    def _create_agent(self) -> AgentExecutor:
        # Define the prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert aircraft design assistant. You have access to specialized tools to perform calculations. Use them when necessary to answer user questions accurately."),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])

        # Create the agent
        agent = create_tool_calling_agent(self.llm, self.tools, prompt)

        # Create the executor
        return AgentExecutor(agent=agent, tools=self.tools, verbose=True)

    async def ainvoke(self, input_text: str) -> dict:
        """
        Asynchronously invoke the agent with the given input.
        """
        return await self.agent_executor.ainvoke({"input": input_text})

    async def astream(self, input_text: str):
        """
        Asynchronously stream the agent's events.
        """
        async for event in self.agent_executor.astream_events(
            {"input": input_text},
            version="v1",
        ):
            yield event

    def invoke(self, input_text: str) -> dict:
        """
        Synchronously invoke the agent with the given input.
        """
        return self.agent_executor.invoke({"input": input_text})
