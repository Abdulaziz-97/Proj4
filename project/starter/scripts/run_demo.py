import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Ensure imports resolve from project root
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from agentic.workflow import invoke_ticket  # noqa: E402
from agentic.logging_config import get_logger, configure_logging  # noqa: E402


def run_case(message: str, thread_id: str, user_id: str = "user-demo") -> None:
    logger = get_logger("demo")
    logger.info("demo_start", extra={"agent": "supervisor", "status": "start", "ticket_id": thread_id})
    result = invoke_ticket(ticket_id=thread_id, user_id=user_id, user_message=message, channel="chat")
    logger.info("demo_end", extra={"agent": "supervisor", "status": "end", "ticket_id": thread_id})
    print(f"\n=== Demo: {message} ===\n")
    print(result["final_text"])


if __name__ == "__main__":
    configure_logging(log_path="logs/agentic.log")

    # Knowledge route example
    run_case("How do I reset my password?", "thread-knowledge", user_id="user-100")

    # Account operations route example
    run_case("I need help with my subscription status", "thread-account", user_id="user-200")

    # Escalation-style example (refund)
    run_case("I was charged twice and need a refund", "thread-escalation", user_id="user-300")

    # Session continuity (two turns in one thread)
    run_case("I can't log in to my account.", "thread-session", user_id="user-400")
    run_case("It still fails after trying the steps.", "thread-session", user_id="user-400")

