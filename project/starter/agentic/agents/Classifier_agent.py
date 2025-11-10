from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
import os
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL")

def create_classifier_agent(llm: ChatOpenAI):
    """Classifies tickets by category and urgency"""
    system_prompt = """
You are a ticket classifier.

Analyze the ticket and return JSON with:
- category: technical/billing/account/reservation/general
- urgency: low/medium/high/critical
- keywords: list of relevant keywords
- recommended_agent: knowledge/account_ops/escalation

Rules:
- "blocked" or "refund" → critical urgency, escalation
- "how to" questions → knowledge agent
- Account queries → account_ops agent
"""
    
    return create_react_agent(
        llm,
        tools=[],  # No tools - pure classification
        state_modifier=system_prompt,
        api_key=api_key,
        base_url=base_url,
        model="gpt-4o-mini",
    )