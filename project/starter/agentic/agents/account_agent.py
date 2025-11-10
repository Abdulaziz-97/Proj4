from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
from agentic.tools import ACCOUNT_TOOLS
import os

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL")
def create_account_agent(llm: ChatOpenAI):
    """Performs account operations"""
    system_prompt = """
    You are a account agent.
    You are responsible for performing account operations.
    You have the following tools available to you:
    {ACCOUNT_TOOLS}
    You should use the tools to perform account operations.
    You should then return the result of the account operation to the user.
    You should also return the confidence score for the account operation.
    You should also return the account operation id for the account operation.
    You should also return the account operation title for the account operation.
    You should also return the account operation content for the account operation.
    You should also return the account operation url for the account operation.
    You should also return the account operation confidence score for the account operation.
    You should also return the account operation id for the account operation.
    You should also return the account operation title for the account operation.
    You should also return the account operation content for the account operation.
    You should also return the account operation url for the account operation.
    """
    return create_react_agent(
        llm=llm,
        tools=ACCOUNT_TOOLS,
        state_modifier=system_prompt,
        api_key=api_key,
        base_url=base_url,
        model="gpt-4o-mini",
    )