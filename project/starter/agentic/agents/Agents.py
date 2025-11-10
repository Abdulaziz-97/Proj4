"""# UDA-Hub Multi-Agent Architecture

## System Purpose
Intelligent customer support ticket resolution system for CultPass 
using multi-agent orchestration with LangGraph.

## Design Pattern
Supervisor Pattern with Specialized Workers

## Key Design Decisions
- Why supervisor pattern? [explain your reasoning]
- How many agents? [explain your choice]
- What triggers escalation? [define criteria]
Agent 1: Supervisor/Orchestrator
Role: Receives ticket, routes to appropriate worker, aggregates responses
Decision criteria:
Analyzes ticket content for keywords
Checks ticket metadata (urgency, user history)
Determines which specialist(s) to call
Does NOT: Directly resolve issues (delegates to workers)

Agent 2: Classifier Agent (optional but recommended)
Role: Analyzes ticket and extracts:
Issue category (technical, billing, account, reservation)
Urgency level (low, medium, high, critical)
Required actions (lookup, modify, escalate)
Output: Structured classification data for routing
Tools: None (pure LLM reasoning)

Agent 3: Knowledge Retrieval Agent
Role: Searches knowledge base for relevant articles
Tools:
search_knowledge_base(query, tags) - finds articles
Logic:
Performs semantic/keyword search
Scores relevance/confidence
If confidence > 0.7: returns article-based response
If confidence < 0.7: signals need for escalation
Output: Response text OR escalation flag

Agent 4: Account Operations Agent
Role: Performs database lookups and operations
Tools:
lookup_user_account(user_id) - get user details
check_subscription_status(user_id) - subscription info
get_user_reservations(user_id) - active bookings
cancel_reservation(reservation_id) - cancel booking
update_subscription(user_id, action) - pause/cancel sub
Logic: Executes when supervisor determines data lookup/action needed
Output: Structured data or action confirmation

Agent 5: Escalation Agent
Role: Handles cases requiring human intervention
Triggers:
No knowledge article found
Confidence too low
User account blocked
Refund requests (policy exception)
Security concerns
Actions:
Logs escalation reason
Summarizes ticket for human agent
Updates ticket status to "escalated"
Output: Escalation summary"""

from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import Tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.graph import MermaidDrawMethod
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.types import Command
from langgraph.graph.message import MessagesState
from langgraph.types import Command
from langchain_openai import ReActChatOpenAI

from dotenv import load_dotenv
import os

load_dotenv()

supervisor = ReActChatOpenAI(
    name="Supervisor",
    model="gpt-4o-mini",
    temperature=0.0,
    api_key=os.getenv("VOCAREUM_API_KEY"),
    base_url="https://openai.vocareum.com/v1"
)

classifier_agent = ReActChatOpenAI(
    name="Classifier Agent",
    model="gpt-4o-mini",
    temperature=0.0,
    api_key=os.getenv("VOCAREUM_API_KEY"),
    base_url="https://openai.vocareum.com/v1"
)

knowledge_retrieval_agent = ReActChatOpenAI(
    name="Knowledge Retrieval Agent",
    model="gpt-4o-mini",
    temperature=0.0,
    api_key=os.getenv("VOCAREUM_API_KEY"),
    base_url="https://openai.vocareum.com/v1"
)

account_operations_agent = ReActChatOpenAI(
    name="Account Operations Agent",
    model="gpt-4o-mini",
    temperature=0.0,
    api_key=os.getenv("VOCAREUM_API_KEY"),
    base_url="https://openai.vocareum.com/v1"
)

escalation_agent = ReActChatOpenAI(
    name="Escalation Agent",
    model="gpt-4o-mini",
    temperature=0.0,
    api_key=os.getenv("VOCAREUM_API_KEY"),
    base_url="https://openai.vocareum.com/v1"
)


