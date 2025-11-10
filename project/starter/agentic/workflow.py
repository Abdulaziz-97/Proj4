import json
import os
from typing import Any, Dict, List

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, BaseMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph_supervisor import create_supervisor

from agentic.agents.classifier_agent import create_classifier_agent
from agentic.agents.knowledge_agent import create_knowledge_agent
from agentic.agents.account_agent import create_account_agent
from agentic.agents.escalation_agent import create_escalation_agent
from agentic.logging_config import configure_logging, get_logger
from agentic.state import create_initial_state
from agentic.memory_manager import get_contextualized_state
from agentic.tools.memory_tools import add_ticket_message, update_ticket_status


# ===== Environment & Logging =====
load_dotenv()
configure_logging(log_path="logs/agentic.log")
logger = get_logger("workflow")


# ===== LLM (shared) =====
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
llm = ChatOpenAI(
    model=OPENAI_MODEL,
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
)

# ===== Checkpointer (session memory) =====
checkpointer = MemorySaver()


# ===== Build Supervisor Graph =====
supervisor_prompt = SystemMessage(
    content=(
        "You are the Supervisor in a multi-agent customer support system.\n"
        "- Classify the ticket and route to the best agent: knowledge, account_ops, or escalation.\n"
        "- Prefer knowledge for informational/how-to queries.\n"
        "- Prefer account_ops for account, subscription, billing changes, or reservations.\n"
        "- Escalate when confidence is low, refund/charge disputes, blocked accounts, or anything requiring human review.\n"
        "When an agent hands back, decide whether to route again or finish. Keep the conversation grounded and concise."
    )
)

# Create workers (named)
classifier = create_classifier_agent(llm)
knowledge = create_knowledge_agent(llm)
account_ops = create_account_agent(llm)
escalation = create_escalation_agent(llm)

# Compile supervisor
supervisor = create_supervisor(
    model=llm,
    agents=[classifier, knowledge, account_ops, escalation],
    prompt=supervisor_prompt,
    add_handoff_back_messages=True,
    output_mode="last_message",
    name="supervisor",
).compile(checkpointer=checkpointer, name="supervisor")


# ===== Helpers =====
def _extract_last_assistant(messages: List[BaseMessage]) -> str:
    for msg in reversed(messages):
        try:
            if getattr(msg, "type", None) == "ai" or msg.__class__.__name__ == "AIMessage":
                return str(msg.content)
        except Exception:
            continue
    return str(messages[-1].content) if messages else ""


def _detect_escalation(messages: List[BaseMessage]) -> bool:
    text = " ".join([str(getattr(m, "content", "")) for m in messages]).lower()
    keywords = ["escalat", "hand off", "hand-off", "human support", "billing team ticket"]
    return any(k in text for k in keywords)



def invoke_ticket(
    ticket_id: str,
    user_id: str,
    user_message: str,
    channel: str = "chat",
    thread_id: str | None = None,
) -> Dict[str, Any]:
    """
    Run a ticket end-to-end through the Supervisor with memory and logging.
    Returns a dict with final_text.
    """
    thread = thread_id or ticket_id
    logger.info(
        "ticket_start",
        extra={"ticket_id": ticket_id, "user_id": user_id, "agent": "supervisor", "status": "start"},
    )

    # Create initial state and enrich with long-term memory context
    state = create_initial_state(ticket_id=ticket_id, user_id=user_id, user_message=user_message, channel=channel)
    state = get_contextualized_state(state, include_history=True)

    # Invoke supervisor with session memory
    result = supervisor.invoke(
        {"messages": state["messages"]},
        config={"configurable": {"thread_id": thread}},
    )

    # With output_mode="last_message", result is the last assistant message/content
    final_text = str(result)

    # Persist memory (long-term)
    try:
        add_ticket_message.invoke({"ticket_id": ticket_id, "role": "ai", "content": final_text})
        status = "escalated" if ("escalat" in final_text.lower() or "billing team" in final_text.lower()) else "resolved"
        update_ticket_status.invoke({"ticket_id": ticket_id, "status": status})
    except Exception as e:
        logger.info("memory_persist_error", extra={"ticket_id": ticket_id, "agent": "supervisor", "status": str(e)})

    logger.info(
        "ticket_end",
        extra={"ticket_id": ticket_id, "user_id": user_id, "agent": "supervisor", "status": "end"},
    )
    return {"final_text": final_text}
