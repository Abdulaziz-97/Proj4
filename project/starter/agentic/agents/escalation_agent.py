from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
import os
from agentic.tools import ESCALATION_TOOLS
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL")
def create_escalation_agent(llm: ChatOpenAI):
    """Performs escalation operations"""
    system_prompt = """
    You are a escalation agent.
    You are responsible for performing escalation operations.
    You have the following tools available to you:
    {ESCALATION_TOOLS}
    You should use the tools to perform escalation operations.
    You should then return the result of the escalation operation to the user.
    You should also return the confidence score for the escalation operation.
    You should also return the escalation operation id for the escalation operation.
    You should also return the escalation operation title for the escalation operation.
    You should also return the escalation operation content for the escalation operation.
    You should also return the escalation operation url for the escalation operation.
    You should also return the escalation operation confidence score for the escalation operation.
    
    """
    return create_react_agent(
        llm=llm,
        tools=ESCALATION_TOOLS,
        state_modifier=system_prompt,
        api_key=api_key,
        base_url=base_url,
        model="gpt-4o-mini",
    )