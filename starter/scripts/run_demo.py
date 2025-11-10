import os
import sys
from dotenv import load_dotenv

load_dotenv()
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from agentic.workflow import supervisor  # noqa: E402
from agentic.logging_config import get_logger  # noqa: E402


def run_case(message: str, thread_id: str) -> None:
    logger = get_logger("demo")
    logger.info("demo_start", extra={"agent": "supervisor", "status": "start", "thread": thread_id})
    result = supervisor.invoke(
        {"messages": [("user", message)]},
        config={"configurable": {"thread_id": thread_id}},
    )
    logger.info("demo_end", extra={"agent": "supervisor", "status": "end", "thread": thread_id})
    print(f"\n=== Demo: {message} ===\n")
    print(result)


if __name__ == "__main__":
    run_case("How do I reset my password?", "thread-knowledge")
    run_case("I need help with my subscription status", "thread-account")
    run_case("I was charged twice and need a refund", "thread-escalation")


