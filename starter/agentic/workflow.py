from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph_supervisor import create_supervisor
import os

from dotenv import load_dotenv
from agentic.logging_config import configure_logging, get_logger
load_dotenv()
configure_logging()
logger = get_logger("workflow")

from agentic.agents.classifier_agent import create_classifier_agent
from agentic.agents.knowledge_agent import create_knowledge_agent
from agentic.agents.account_agent import create_account_agent
from agentic.agents.escalation_agent import create_escalation_agent

# Reuse a single LLM instance for all agents
llm = ChatOpenAI(model="gpt-4o-mini", base_url=os.getenv("OPENAI_BASE_URL"))

supervisor = create_supervisor(
    model=llm,
    checkpointer=MemorySaver(),
    agents=[
        create_classifier_agent(llm),
        create_knowledge_agent(llm),
        create_account_agent(llm),
        create_escalation_agent(llm)
    ],
    prompt=SystemMessage(content="""
    You are a supervisor for the customer support system.
    Route to the best agent, monitor progress, and ensure resolution.
    """),
    add_handoff_back_messages=True,
    output_mode="last_message",
    name="supervisor",
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
).compile(checkpointer=MemorySaver(), name="supervisor")

if __name__ == "__main__":
    payload = {"messages": [("user", "I need help with my account")]}
    cfg = {"configurable": {"thread_id": "demo-thread-1"}}
    logger.info("Invoke supervisor", extra={"status": "start", "agent": "supervisor"})
    result = supervisor.invoke(payload, config=cfg)
    logger.info("Supervisor finished", extra={"status": "end", "agent": "supervisor"})
    print(result)