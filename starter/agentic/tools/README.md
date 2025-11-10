# UDA-Hub Tools Documentation

This directory contains all tools used by the multi-agent support system. Tools provide database abstraction and enable agents to perform operations.

## Overview

### Tool Categories

1. **Knowledge Tools** - Search and retrieve support articles
2. **Account Tools** - User account operations and lookups
3. **Memory Tools** - Ticket history and interaction tracking

## Tool Inventory

### Knowledge Base Tools (3 tools)

#### `search_knowledge_base(query, tags, account_id)`
- **Purpose**: Search knowledge base for relevant articles
- **Returns**: Articles with relevance scores and confidence
- **Use Case**: Primary tool for answering FAQ-type questions
- **Example**: `search_knowledge_base(query="how to login", tags="login,password")`

#### `get_article_by_id(article_id)`
- **Purpose**: Retrieve specific article by ID
- **Returns**: Complete article details
- **Use Case**: Follow-up when article ID is known

#### `list_knowledge_categories(account_id)`
- **Purpose**: List all available categories/tags
- **Returns**: Categories with article counts
- **Use Case**: Browsing available topics

---

### Account Management Tools (5 tools)

#### `lookup_user_account(user_id)`
- **Purpose**: Get comprehensive user information
- **Returns**: User details, subscription, reservations, alerts
- **Use Case**: Customer asks "what's my account status?"
- **Example**: `lookup_user_account(user_id="a4ab87")`
- **⚠️ IMPORTANT**: Flags blocked users for escalation

#### `check_subscription_status(user_id)`
- **Purpose**: Detailed subscription information
- **Returns**: Status, tier, quota usage, billing dates
- **Use Case**: Subscription-specific queries
- **Example**: `check_subscription_status(user_id="f556c0")`

#### `get_user_reservations(user_id, include_cancelled)`
- **Purpose**: List user's bookings with experience details
- **Returns**: Reservations with event information
- **Use Case**: "Show me my upcoming events"
- **Example**: `get_user_reservations(user_id="a4ab87")`

#### `cancel_reservation(reservation_id)`
- **Purpose**: Cancel a booking
- **Returns**: Cancellation confirmation
- **Use Case**: Customer wants to cancel reservation
- **Example**: `cancel_reservation(reservation_id="abc123")`
- **Note**: Automatically restores quota

#### `update_subscription_status(subscription_id, action)`
- **Purpose**: Pause or cancel subscription
- **Returns**: Update confirmation
- **Use Case**: Subscription management
- **Example**: `update_subscription_status(subscription_id="sub123", action="cancel")`
- **⚠️ NOTE**: Refund requests require escalation

---

### Memory & Ticket Tools (5 tools)

#### `get_user_ticket_history(external_user_id, limit, account_id)`
- **Purpose**: Retrieve past ticket history (long-term memory)
- **Returns**: Previous tickets with summaries
- **Use Case**: Personalizing support based on history
- **Example**: `get_user_ticket_history(external_user_id="a4ab87", limit=5)`

#### `get_ticket_details(ticket_id)`
- **Purpose**: Get complete ticket with all messages
- **Returns**: Full conversation thread
- **Use Case**: Reviewing specific ticket details

#### `update_ticket_status(ticket_id, status, main_issue_type)`
- **Purpose**: Update ticket status and classification
- **Returns**: Update confirmation
- **Use Case**: Marking tickets as resolved/escalated
- **Example**: `update_ticket_status(ticket_id="123", status="resolved", main_issue_type="technical")`

#### `add_ticket_message(ticket_id, role, content)`
- **Purpose**: Add message to ticket (for logging)
- **Returns**: Message creation confirmation
- **Use Case**: Recording AI responses in ticket history
- **Example**: `add_ticket_message(ticket_id="123", role="ai", content="Solution provided")`

#### `create_escalation_ticket(external_user_id, issue_summary, reason)`
- **Purpose**: Create ticket for human review
- **Returns**: Escalation ticket details
- **Use Case**: Issues requiring human intervention
- **Example**: `create_escalation_ticket(external_user_id="a4ab87", issue_summary="Refund request", reason="refund_request")`

---

## Usage in Agents

### Import Tools

```python
from agentic.tools import (
    search_knowledge_base,
    lookup_user_account,
    get_user_ticket_history,
    KNOWLEDGE_TOOLS,
    ACCOUNT_TOOLS,
    ALL_TOOLS
)
```

### Using Tool Collections

```python
# Knowledge Agent gets knowledge tools
knowledge_agent = create_react_agent(
    model=llm,
    tools=KNOWLEDGE_TOOLS,
    prompt=knowledge_prompt
)

# Account Agent gets account tools
account_agent = create_react_agent(
    model=llm,
    tools=ACCOUNT_TOOLS,
    prompt=account_prompt
)

# Supervisor might need all tools
supervisor = create_supervisor(
    model=llm,
    agents=[knowledge_agent, account_agent],
    tools=ALL_TOOLS  # Can access any tool if needed
)
```

---

## Database Abstraction

All tools use `DatabaseManager` for connection handling:

```python
from agentic.tools import get_db_manager

db = get_db_manager()

# CultPass database (external user data)
with db.get_cultpass_session() as session:
    user = session.query(cultpass.User).filter_by(user_id=user_id).first()

# UdaHub database (support system data)
with db.get_udahub_session() as session:
    ticket = session.query(udahub.Ticket).filter_by(ticket_id=ticket_id).first()
```

---

## Error Handling

All tools return JSON strings with consistent error format:

```json
{
    "success": false,
    "error": "Descriptive error message",
    "found": false
}
```

Success responses vary by tool but always include relevant data.

---

## Escalation Triggers

Tools automatically identify situations requiring escalation:

1. **User Account Blocked** → `lookup_user_account` flags this
2. **No Knowledge Found** → `search_knowledge_base` sets `should_escalate: true`
3. **Refund Requests** → `update_subscription_status` notes escalation needed
4. **Low Confidence** → `search_knowledge_base` confidence < 0.5

---

## Testing Tools

Test each tool independently before integration:

```python
# Test knowledge search
result = search_knowledge_base.invoke({
    "query": "how to login",
    "tags": "login"
})
print(result)

# Test account lookup
result = lookup_user_account.invoke({
    "user_id": "a4ab87"
})
print(result)

# Test ticket history
result = get_user_ticket_history.invoke({
    "external_user_id": "f556c0",
    "limit": 3
})
print(result)
```

---

## Tool Statistics

- **Total Tools**: 13
- **Knowledge Tools**: 3
- **Account Tools**: 5
- **Memory Tools**: 5
- **Databases Accessed**: 2 (CultPass, UdaHub)
- **Operations**: Read (9), Write (4)

---

## Next Steps

1. ✅ Tools implemented
2. ⏳ Create agents that use these tools
3. ⏳ Build workflow orchestration
4. ⏳ Implement logging around tool usage
5. ⏳ Test end-to-end with real scenarios
