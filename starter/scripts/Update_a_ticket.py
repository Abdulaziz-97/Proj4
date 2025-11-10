import json
import os
from dotenv import load_dotenv

load_dotenv()

# Ensure project root on path
import sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from agentic.memory_manager import MemoryManager  # noqa: E402
from agentic.tools.memory_tools import get_user_ticket_history, get_ticket_details  # noqa: E402


def find_demo_user(candidates=None):
    if candidates is None:
        candidates = ["a4ab87", "demo_user", "user_1", "u1"]
    for uid in candidates:
        res = json.loads(get_user_ticket_history.invoke({"external_user_id": uid, "limit": 3}))
        if res.get("found") and res.get("tickets"):
            return uid, res
    return None, None


def main():
    user_id, history = find_demo_user()
    if not user_id:
        print("No demo user with history found. Please run the DB setup notebooks first.")
        return

    print(f"Found demo user: {user_id}")
    print(f"Tickets retrieved: {history['total_tickets_retrieved']}")
    first_ticket = history["tickets"][0]["ticket_id"]
    print(f"Using ticket: {first_ticket}")

    # Show details before
    before = json.loads(get_ticket_details.invoke({"ticket_id": first_ticket}))
    print("\nBefore (status):", before.get("status"))
    print("Before (messages):", before.get("message_count"))

    # Store a demo interaction (persistent memory)
    mm = MemoryManager()
    ok = mm.store_interaction(
        ticket_id=first_ticket,
        user_id=user_id,
        category="account",
        resolution="Demo: Provided account assistance and confirmed settings.",
        status="resolved",
    )
    print("\nStored interaction:", ok)

    # Show details after
    after = json.loads(get_ticket_details.invoke({"ticket_id": first_ticket}))
    print("\nAfter (status):", after.get("status"))
    print("After (messages):", after.get("message_count"))

    # Show user history summary again
    updated_hist = json.loads(get_user_ticket_history.invoke({"external_user_id": user_id, "limit": 3}))
    print("\nUpdated insight:", updated_hist.get("insight"))


if __name__ == "__main__":
    main()


