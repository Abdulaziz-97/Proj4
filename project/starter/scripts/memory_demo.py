import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Ensure imports resolve from project root
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from agentic.memory_manager import get_memory_manager  # noqa: E402
from agentic.logging_config import configure_logging  # noqa: E402


def main() -> None:
    configure_logging(log_path="logs/agentic.log")
    memory = get_memory_manager()

    user_id = "user-mem-1"
    ticket_id = "ticket-mem-1"

    print("=== Before storing interaction ===")
    history_before = memory.get_user_history(user_id, limit=5)
    print(history_before)

    print("\n=== Storing interaction ===")
    ok = memory.store_interaction(
        ticket_id=ticket_id,
        user_id=user_id,
        category="account",
        resolution="User guided to reset password via email link.",
        status="resolved",
    )
    print(f"Stored: {ok}")

    print("\n=== After storing interaction ===")
    history_after = memory.get_user_history(user_id, limit=5)
    print(history_after)


if __name__ == "__main__":
    main()
