from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
from agentic.tools import KNOWLEDGE_TOOLS
import os
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL")
def create_knowledge_agent(llm: ChatOpenAI):
    """Searches the knowledge base for relevant articles"""
    system_prompt = """
    You are a knowledge agent.
    You are responsible for searching the knowledge base for relevant articles.
    You are also responsible for returning the most relevant article to the user.
    You have the following tools available to you:
    {KNOWLEDGE_TOOLS}
    You should use the tools to search the knowledge base for relevant articles.
    You should then return the most relevant article to the user.
    You should also return the confidence score for the article.
    You should also return the article id for the article.
    You should also return the article title for the article.
    You should also return the article content for the article.
    You should also return the article url for the article.
    """
   
   
    return create_react_agent(
        llm=llm,
        tools=KNOWLEDGE_TOOLS,
        state_modifier=system_prompt,
        api_key=api_key,
        base_url=base_url,
        model="gpt-4o-mini",
    )