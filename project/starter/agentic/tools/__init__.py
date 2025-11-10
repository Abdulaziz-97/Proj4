"""
UDA-Hub Tools Package
Provides all tools for the multi-agent support system
"""

# Import all tools for easy access
from agentic.tools.knowledge_tools import (
    search_knowledge_base,
    get_article_by_id,
    list_knowledge_categories
)

from agentic.tools.account_tools import (
    lookup_user_account,
    check_subscription_status,
    get_user_reservations,
    cancel_reservation,
    update_subscription_status
)

from agentic.tools.memory_tools import (
    get_user_ticket_history,
    get_ticket_details,
    update_ticket_status,
    add_ticket_message,
    create_escalation_ticket
)

from agentic.tools.db_manager import get_db_manager, DatabaseManager

# Organize tools by category
KNOWLEDGE_TOOLS = [
    search_knowledge_base,
    get_article_by_id,
    list_knowledge_categories
]

ACCOUNT_TOOLS = [
    lookup_user_account,
    check_subscription_status,
    get_user_reservations,
    cancel_reservation,
    update_subscription_status
]

MEMORY_TOOLS = [
    get_user_ticket_history,
    get_ticket_details,
    update_ticket_status,
    add_ticket_message,
    create_escalation_ticket
]

# All tools combined
ALL_TOOLS = KNOWLEDGE_TOOLS + ACCOUNT_TOOLS + MEMORY_TOOLS

__all__ = [
    # Tools
    'search_knowledge_base',
    'get_article_by_id',
    'list_knowledge_categories',
    'lookup_user_account',
    'check_subscription_status',
    'get_user_reservations',
    'cancel_reservation',
    'update_subscription_status',
    'get_user_ticket_history',
    'get_ticket_details',
    'update_ticket_status',
    'add_ticket_message',
    'create_escalation_ticket',
    # Database
    'get_db_manager',
    'DatabaseManager',
    # Tool collections
    'KNOWLEDGE_TOOLS',
    'ACCOUNT_TOOLS',
    'MEMORY_TOOLS',
    'ALL_TOOLS'
]

